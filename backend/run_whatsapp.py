"""
Run script for the WhatsApp ingestion system.

Usage (from backend/):
    python run_whatsapp.py
"""

import sys
import urllib.request
import urllib.error

BACKEND_URL = "http://127.0.0.1:8000/health"


def check_backend() -> bool:
    try:
        with urllib.request.urlopen(BACKEND_URL, timeout=3) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError):
        return False


def main() -> None:
    print("=" * 60)
    print("  EchoMind — WhatsApp Ingestion System")
    print("=" * 60)

    reachable = check_backend()
    if reachable:
        print(f"\n[OK] Backend is already running at {BACKEND_URL}")
    else:
        print(f"\n[--] Backend not detected at {BACKEND_URL}")

    print("""
Steps to start the full system:

  1. Start Python backend  (run from backend/):

       uvicorn app.api.whatsapp_receiver:app --host 127.0.0.1 --port 8000 --reload

  2. Start Node service  (in a separate terminal):

       cd api/whatsapp
       npm start

  3. Scan the QR code that appears in the Node terminal.

  4. Send a WhatsApp message to your number.

  5. Verify ingestion:

       python -m tests.test_whatsapp_connector

  6. Check the database:

       SELECT external_message_id, content_type, raw_content
         FROM memory_chunks ORDER BY created_at DESC LIMIT 10;

       SELECT original_filename, media_type, local_path
         FROM media_files ORDER BY id DESC LIMIT 5;
""")

    if not reachable:
        print("[hint] Start the backend first, then the Node service.")
        sys.exit(0)


if __name__ == "__main__":
    main()
