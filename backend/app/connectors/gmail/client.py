"""
Gmail connector client.

Authenticates via OAuth and returns NormalizedInput objects ready for the
ingestion pipeline. No DB writes, no MediaService calls — connector is pure.

Run from backend/:
    python -m app.connectors.gmail.test_client
"""

import base64
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from models.normalized_input import NormalizedInput, PendingMedia
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# backend/app/connectors/gmail/client.py → parents[3] = backend/
_SECRETS_DIR = Path(__file__).parents[3] / "secrets"
CREDENTIALS_PATH = _SECRETS_DIR / "credentials.json"
TOKEN_PATH = _SECRETS_DIR / "token.json"


def _get_service():
    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {CREDENTIALS_PATH}. "
                    "Download it from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds)


_NOISE_KEYWORDS = (
    "unsubscribe",
    "privacy",
    "terms",
    "all rights reserved",
    "\u00a9",  # ©
)


def _decode(data: str) -> str:
    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    lines = soup.get_text(separator="\n").splitlines()
    return "\n".join(line.strip() for line in lines if line.strip())


def remove_noise(text: str) -> str:
    clean = []
    for line in text.splitlines():
        lower = line.lower()
        if not any(kw in lower for kw in _NOISE_KEYWORDS):
            clean.append(line)
    return "\n".join(clean)


def _extract_attachments(service, message: dict) -> list[dict]:
    results = []

    def _walk(parts):
        for part in parts:
            filename = part.get("filename", "")
            if filename:
                body = part.get("body", {})
                attachment_id = body.get("attachmentId")
                if not attachment_id:
                    continue
                resp = (
                    service.users()
                    .messages()
                    .attachments()
                    .get(userId="me", messageId=message["id"], id=attachment_id)
                    .execute()
                )
                raw = resp.get("data", "")
                if raw:
                    results.append({
                        "filename":  filename,
                        "mime_type": part.get("mimeType", "application/octet-stream"),
                        "data":      base64.urlsafe_b64decode(raw),
                    })
            # Recurse into nested multipart containers.
            if part.get("parts"):
                _walk(part["parts"])

    _walk(message["payload"].get("parts", []))
    return results


def _extract_body(payload: dict) -> str:
    # Simple (non-multipart) email: data sits directly on the body.
    direct = payload.get("body", {}).get("data")
    if direct and not payload.get("parts"):
        return _decode(direct)

    text_plain = ""
    text_html = ""

    for part in payload.get("parts", []):
        mime = part.get("mimeType", "")
        data = part.get("body", {}).get("data")

        if mime == "text/plain" and data:
            text_plain = _decode(data)
        elif mime == "text/html" and data:
            text_html = _decode(data)
        elif mime.startswith("multipart/"):
            # Recurse into nested multipart sections (e.g. multipart/alternative).
            nested = _extract_body(part)
            if nested:
                text_plain = text_plain or nested

    if text_plain:
        return text_plain

    if text_html:
        return remove_noise(clean_html(text_html))

    return ""


def _header(headers: list[dict], name: str) -> str:
    return next(
        (h["value"] for h in headers if h["name"].lower() == name.lower()), ""
    )


def _parse_date(date_str: str) -> datetime:
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def fetch_recent_emails(limit: int = 50) -> list[NormalizedInput]:
    """
    Fetch the most recent `limit` emails and return NormalizedInput objects.
    Attachments are mapped to PendingMedia (not saved — pipeline's responsibility).
    """
    service = _get_service()

    message_refs = (
        service.users()
        .messages()
        .list(userId="me", maxResults=limit)
        .execute()
        .get("messages", [])
    )

    results = []
    for ref in message_refs:
        msg = service.users().messages().get(
            userId="me", id=ref["id"], format="full"
        ).execute()

        headers    = msg["payload"]["headers"]
        direction  = "sent" if "SENT" in msg.get("labelIds", []) else "received"
        from_addr  = _header(headers, "From")
        to_addr    = _header(headers, "To")
        event_time = _parse_date(_header(headers, "Date"))
        attachments = _extract_attachments(service, msg)

        participants = [p for p in [from_addr, to_addr] if p]

        media = [
            PendingMedia(
                raw_bytes=att["data"],
                original_filename=att["filename"],
                mime_type=att["mime_type"],
                captured_at=event_time,
            )
            for att in attachments
        ]

        results.append(NormalizedInput(
            source_type="gmail",
            external_id=msg["id"],
            content=_extract_body(msg["payload"]),
            content_type="email",
            event_time=event_time,
            participants=participants,
            metadata={
                "subject":          _header(headers, "Subject"),
                "thread_id":        msg["threadId"],
                "direction":        direction,
                "has_attachments":  len(attachments) > 0,
                "attachment_count": len(attachments),
            },
            media=media,
        ))

    return results
