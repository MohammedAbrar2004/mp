import os
import sys

# Adjust path so imports work
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../../../"))
sys.path.append(PROJECT_ROOT)

# Import your processors
from app.preprocessing.services.media.pdf_processor import extract_text_from_pdf
from app.preprocessing.services.media.audio_processor import transcribe_audio


def test_pdf(file_path):
    print("\n===== PDF TEST =====")

    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    try:
        text = extract_text_from_pdf(file_path, "application/pdf")

        if text:
            print("\n--- Extracted Text ---\n")
            print(text[:1000])  # limit output
            print(f"\n[Length: {len(text)} characters]")
        else:
            print("\nNo text extracted (likely scanned PDF → needs OCR)")

    except Exception as e:
        print(f"PDF ERROR: {e}")


def test_audio(file_path):
    print("\n===== AUDIO TEST =====")

    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    try:
        text = transcribe_audio(file_path, "audio/ogg")

        if text:
            print("\n--- Transcription ---\n")
            print(text)
            print(f"\n[Length: {len(text)} characters]")
        else:
            print("\nNo transcription returned (check ffmpeg / decoding)")

    except Exception as e:
        print(f"AUDIO ERROR: {e}")


if __name__ == "__main__":
    # 🔁 CHANGE THESE PATHS FOR TESTING
    pdf_file = "sample.pdf"
    audio_file = "sample.ogg"

    test_pdf(pdf_file)
    test_audio(audio_file)