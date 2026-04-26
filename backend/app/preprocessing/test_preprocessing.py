from app.preprocessing.services.salience.salience_service import compute_salience

test_data = [
    # -------- HIGH VALUE (structured conversations) --------
    ("Amaan: We need to finalize the ML report and submit it by Friday evening. Let's review it tomorrow at 3pm.", False),
    ("Client meeting scheduled on 12/02/2026 at 11am. Prepare presentation and confirm attendance.", False),
    ("Reminder: submit project documentation, update README, and push final code before deadline.", False),

    # -------- MEDIUM VALUE (normal useful chats) --------
    ("I completed preprocessing module, working on embeddings now.", False),
    ("Let's sync later today and discuss next steps.", False),
    ("I think we should improve the UI dashboard for better visualization.", False),

    # -------- MEDIA CASE --------
    ("See attached document for project architecture and flow diagrams.", True),
    ("Sharing meeting notes PDF, please review before tomorrow's call.", True),

    # -------- LOW VALUE (casual chats) --------
    ("ok bro", False),
    ("lol 😂", False),
    ("nice", False),

    # -------- EDGE CASES --------
    ("URGENT: need to call client ASAP regarding deadline extension", False),
    ("Meeting postponed", False),
    ("Tomorrow", False),
]


def run_test():
    print("\n=== ADVANCED PREPROCESSING TEST OUTPUT ===\n")

    for i, (text, has_media) in enumerate(test_data, 1):
        score = compute_salience(text, {}, has_media)

        if score is None:
            level = "ERROR"
        elif score < 0.3:
            level = "LOW"
        elif score < 0.6:
            level = "MEDIUM"
        else:
            level = "HIGH"

        print(f"{i}. [{level}] {score:.2f}")
        print(f"   {text}\n")


if __name__ == "__main__":
    run_test()