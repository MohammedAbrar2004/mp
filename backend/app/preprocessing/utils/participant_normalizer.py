"""
Participant Normalizer

Purpose:
    Convert platform-specific participant identifiers (emails, JIDs)
    into consistent human-readable names for semantic layer.
"""

PARTICIPANT_MAP = {
    # WhatsApp JIDs
    "918888888888@wa": "Amaan",
    "919999999999@wa": "Abrar",
    "917777777777@wa": "Abdullah",

    # Emails
    "amaan@gmail.com": "Amaan",
    "abrar@gmail.com": "Abrar",
    "abdullah@gmail.com": "Abdullah",
    "maam@university.edu": "Ma'am",

    # fallback names
    "Amaan": "Amaan",
    "Abrar": "Abrar",
    "Abdullah": "Abdullah",
    "Ma'am": "Ma'am",
    "Hadi": "Hadi",
}


def normalize_participants(participants):
    """
    Normalize participants list into consistent names.

    Input:
        ["918888@wa", "amaan@gmail.com"]

    Output:
        ["Amaan"]
    """
    if not participants:
        return []

    normalized = set()

    for p in participants:
        name = PARTICIPANT_MAP.get(p, p)
        normalized.add(name)

    return list(normalized)