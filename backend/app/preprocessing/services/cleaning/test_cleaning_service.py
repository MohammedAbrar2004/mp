import logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)-8s %(name)s — %(message)s")

from app.preprocessing.services.cleaning.cleaning_service import clean_content
from app.preprocessing.services.cleaning.heuristic_rules import (
    heuristic_clean,
    compute_noise_score,
    is_readable,
    should_use_llm,
)
from app.preprocessing.services.cleaning.emoji_normalization import normalize_emojis
from app.preprocessing.services.cleaning.text_cleaning import clean_text_content

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def section(title: str):
    print(f"\n{'=' * 72}")
    print(f"  {title}")
    print('=' * 72)

def case(label: str, raw, result):
    print(f"\n  [{label}]")
    print(f"  IN  : {repr(raw[:120])}")
    print(f"  OUT : {repr(result[:120]) if result else repr(result)}")


# ─────────────────────────────────────────────
# 1. heuristic_rules — unit tests
# ─────────────────────────────────────────────

section("1. heuristic_clean")

cases_heuristic = [
    ("extra newlines",      "Hello\n\n\n\n\nWorld"),
    ("extra spaces",        "Hello     World   how  are  you"),
    ("bullet normalization","• Item one\n● Item two\n◦ Item three"),
    ("junk symbols",        "Hello ###$$$ World"),
    ("unicode NFC",         "café"),   # café as decomposed
    ("empty string",        ""),
    ("only spaces",         "     "),
]

for label, raw in cases_heuristic:
    case(label, raw, heuristic_clean(raw))


section("2. compute_noise_score")

noise_cases = [
    ("clean prose",    "The meeting is confirmed for tomorrow at 3pm."),
    ("heavy symbols",  "### @@ $$ %% !! ** ^^ && ** [[]]"),
    ("short tokens",   "ok hi so is it up to me or no"),
    ("empty",          ""),
    ("OCR garbage",    "H3ll0 w0rld!!! @@@ \t\t  ???  ###"),
]

for label, raw in noise_cases:
    score = compute_noise_score(raw)
    readable = is_readable(raw)
    use_llm  = should_use_llm(raw)
    print(f"\n  [{label}]")
    print(f"  text     : {repr(raw[:80])}")
    print(f"  noise    : {score:.3f}  |  readable: {readable}  |  use_llm: {use_llm}")


# ─────────────────────────────────────────────
# 2. emoji_normalization — unit tests
# ─────────────────────────────────────────────

section("3. normalize_emojis")

emoji_cases = [
    ("known emojis",   "Great job 👍 Task ✅ Watch out ❗"),
    ("unknown emoji",  "Let's go 🚀 See you 👋"),
    ("mixed",          "Thanks 🙏 and good luck 🍀"),
    ("no emojis",      "Plain text with no emojis at all."),
    ("empty",          ""),
]

for label, raw in emoji_cases:
    case(label, raw, normalize_emojis(raw))


# ─────────────────────────────────────────────
# 3. text_cleaning — unit tests
# ─────────────────────────────────────────────

section("4. clean_text_content (heuristic + emoji, no LLM)")

text_cases = [
    ("whatsapp style",   "hey!! 👍 meeting tmrw???   \n\n\n sure thing 🙏"),
    ("bullet list",      "• Buy groceries\n● Call doctor\n◦ Fix laptop"),
    ("noisy spacing",    "Hello     how   are   you\n\n\n\nI am  fine"),
    ("emoji heavy",      "✅ Done ❗ Important 🔥 Urgent 😂 Funny"),
    ("empty",            ""),
    ("only whitespace",  "    \n\n   "),
]

for label, raw in text_cases:
    case(label, raw, clean_text_content(raw))


# ─────────────────────────────────────────────
# 4. clean_content — email routing (LLM path)
# ─────────────────────────────────────────────

section("5. clean_content — email (LLM path)")

email_cases = [
    (
        "simple confirmation",
        """<html><body>
            <p>Hi Abrar,</p>
            <p>Just confirming the meeting at 3pm tomorrow.</p>
            <p>Thanks,<br>Amaan</p>
        </body></html>"""
    ),
    (
        "email with signature block",
        """<html><body>
            <p>Hello,</p>
            <p>Please review the attached document before the deadline.</p>
            <hr>
            <p>Best regards,<br>John Smith</p>
            <p>Senior Manager<br>XYZ Corp<br>john@xyz.com</p>
            <p><a href="#">Unsubscribe</a></p>
        </body></html>"""
    ),
    (
        "promotional email",
        """<html><body>
            <p>Hi there!</p>
            <p>Your order #12345 has been shipped and will arrive by Friday.</p>
            <p>Track your order here: <a href="#">Click here</a></p>
            <footer>
                <p>Follow us on Instagram | Twitter | Facebook</p>
                <p>To unsubscribe click here</p>
                <p>© 2024 ShopCo. All rights reserved.</p>
            </footer>
        </body></html>"""
    ),
    (
        "casual email",
        """<html><body>
            <p>Hey bro 😂😂</p>
            <p>Are we still on for the game tonight?</p>
            <p>Let me know!</p>
        </body></html>"""
    ),
    (
        "plain text email (no HTML)",
        "Hi Sarah,\n\nCan you send me the Q3 report by EOD?\n\nThanks,\nMike\n\n--\nMike Johnson | Analyst | mike@corp.com"
    ),
    (
        "empty email",
        ""
    ),
]

for label, raw in email_cases:
    print(f"\n  [{label}]")
    result = clean_content(raw, "email")
    print(f"  OUT : {repr(result[:200])}")


# ─────────────────────────────────────────────
# 5. clean_content — text routing
# ─────────────────────────────────────────────

section("6. clean_content — text routing")

text_routing_cases = [
    ("normal prose",     "The meeting is at 3pm tomorrow in room 204."),
    ("noisy whatsapp",   "yooo 👍👍 u coming tmrw??   \n\n\nyes bro 🙏"),
    ("bullet text",      "• Task 1\n● Task 2\n◦ Task 3"),
    ("empty",            ""),
]

for label, raw in text_routing_cases:
    case(label, raw, clean_content(raw, "text"))


# ─────────────────────────────────────────────
# 6. clean_content — document / audio routing
# ─────────────────────────────────────────────

section("7. clean_content — document routing")

doc_cases = [
    ("OCR output",       "Th1s is a sc4nned d0cument with n0ise and     extra   spaces."),
    ("clean transcript", "The annual report shows a 12% increase in revenue this quarter."),
    ("empty",            ""),
]

for label, raw in doc_cases:
    case(label, raw, clean_content(raw, "document"))

section("8. clean_content — audio routing")

audio_cases = [
    ("transcript",  "um so like the meeting is uh tomorrow at three pm right"),
    ("empty",       ""),
]

for label, raw in audio_cases:
    case(label, raw, clean_content(raw, "audio"))


# ─────────────────────────────────────────────
# 7. clean_content — unknown type fallback
# ─────────────────────────────────────────────

section("9. clean_content — unknown type (heuristic fallback)")

fallback_cases = [
    ("unknown type",   "Hello   world\n\n\n\nThis is   a test.", "calendar"),
    ("another unknown","• Point one\n● Point two",               "sms"),
]

for label, raw, ctype in fallback_cases:
    print(f"\n  [{label}] type='{ctype}'")
    result = clean_content(raw, ctype)
    print(f"  IN  : {repr(raw)}")
    print(f"  OUT : {repr(result)}")


print(f"\n{'=' * 72}")
print("  ALL TESTS COMPLETE")
print('=' * 72 + "\n")
