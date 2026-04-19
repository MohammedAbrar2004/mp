"""
Google Calendar connector client.

Authenticates via OAuth and returns events in a ±30-day window
as NormalizedInput objects. No pipeline, no DB.

Run from backend/:
    python -m app.connectors.calendar.test_client
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from models.normalized_input import NormalizedInput

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

_SECRETS_DIR = Path(__file__).parents[3] / "secrets"
CREDENTIALS_PATH = _SECRETS_DIR / "credentials.json"
TOKEN_PATH = _SECRETS_DIR / "token_calendar.json"


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

    return build("calendar", "v3", credentials=creds)


def _parse_event_time(dt_str: str) -> datetime:
    """Parse ISO dateTime or date string into a UTC-aware datetime."""
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        # All-day events return bare date strings — treat as UTC midnight.
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def fetch_upcoming_events(limit: int = 30) -> list[NormalizedInput]:
    """Fetch calendar events within ±30 days from all calendars as NormalizedInput objects."""
    service = _get_service()

    now = datetime.now(timezone.utc)
    time_min = (now - timedelta(days=30)).isoformat()
    time_max = (now + timedelta(days=30)).isoformat()

    calendar_list = service.calendarList().list().execute()
    calendars = calendar_list.get("items", [])

    all_events = []
    for cal in calendars:
        cal_id = cal["id"]
        events_result = (
            service.events()
            .list(
                calendarId=cal_id,
                maxResults=limit,
                singleEvents=True,
                orderBy="startTime",
                timeMin=time_min,
                timeMax=time_max,
            )
            .execute()
        )
        all_events.extend(events_result.get("items", []))

    normalized_events = []
    for event in all_events:
        start = event["start"].get("dateTime") or event["start"].get("date", "")
        end = event["end"].get("dateTime") or event["end"].get("date", "")

        attendees = [
            a.get("email")
            for a in event.get("attendees", [])
            if a.get("email")
        ]

        participants = attendees if attendees else ["self"]

        normalized_events.append(
            NormalizedInput(
                source_type="calendar",
                external_id=event["id"],
                content=event.get("summary", "No title"),
                content_type="text",
                event_time=_parse_event_time(start) if start else now,
                participants=participants,
                metadata={
                    "event_title": event.get("summary"),
                    "description": event.get("description"),
                    "start":       start,
                    "end":         end,
                    "location":    event.get("location"),
                },
                media=[],
            )
        )

    return normalized_events
