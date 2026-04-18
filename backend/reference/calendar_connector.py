"""
Google Calendar connector for EchoMind.
Fetches upcoming events via Google Calendar API with OAuth authentication.
Extracts event details, normalizes to NormalizedInput format.
"""

import pickle
import logging
from datetime import datetime, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.connectors.base_connector import BaseConnector
from models.normalized_input import NormalizedInput

logger = logging.getLogger("EchoMind.Calendar")


class CalendarConnector(BaseConnector):
    """Google Calendar data connector with OAuth authentication."""
    
    # Calendar API scope - read-only
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    
    # How many days in the future to fetch events
    DAYS_LOOKAHEAD = 30
    
    def __init__(self):
        """Initialize Calendar connector with OAuth credentials."""
        super().__init__()
        self.connector_dir = Path(__file__).parent
        self.credentials_path = self.connector_dir.parent / 'gmail' / 'credentials.json'
        self.token_path = self.connector_dir / 'token.json'
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API using OAuth."""
        creds = None
        
        # Load existing token if available
        if self.token_path.exists():
            with open(self.token_path, 'rb') as token_file:
                creds = pickle.load(token_file)
                logger.info("Calendar: Loaded cached token")
        
        # Refresh or request new credentials
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("Calendar: Token refreshed")
            except Exception as e:
                logger.warning(f"Calendar: Token refresh failed: {e}")
                creds = None
        
        if not creds or not creds.valid:
            if not self.credentials_path.exists():
                raise FileNotFoundError(
                    f"Calendar credentials.json not found at {self.credentials_path}. "
                    "Download it from Google Cloud Console."
                )
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path),
                    self.SCOPES
                )
                creds = flow.run_local_server(port=0)
                
                # Save token for next run
                with open(self.token_path, 'wb') as token_file:
                    pickle.dump(creds, token_file)
                logger.info("Calendar: New token generated and saved")
            except Exception as e:
                raise RuntimeError(f"Calendar OAuth authentication failed: {e}")
        
        self.service = build('calendar', 'v3', credentials=creds)
        logger.info("Calendar: Service initialized")
    
    def fetch_data(self) -> list[NormalizedInput]:
        """
        Fetch upcoming events from Google Calendar.
        Extract event details and create NormalizedInput objects.
        """
        results = []
        
        if not self.service:
            logger.error("Calendar: Not authenticated")
            return results
        
        try:
            # Calculate time window
            now = datetime.utcnow()
            time_min = now.isoformat() + 'Z'
            time_max = (now + timedelta(days=self.DAYS_LOOKAHEAD)).isoformat() + 'Z'
            
            # Fetch events from primary calendar
            events = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime',
                maxResults=50
            ).execute().get('items', [])
            
            logger.info(f"Calendar: Found {len(events)} upcoming events")
            
            for event in events:
                try:
                    # Extract event details
                    event_id = event.get('id', '')
                    title = event.get('summary', '[No Title]')
                    description = event.get('description', '')
                    
                    # Parse event times
                    start_info = event.get('start', {})
                    start_str = start_info.get('dateTime') or start_info.get('date')
                    
                    try:
                        if 'T' in start_str:
                            # DateTime format
                            event_time = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                        else:
                            # Date format (all-day event)
                            event_time = datetime.fromisoformat(start_str)
                    except:
                        event_time = datetime.now()
                    
                    # Extract attendees/participants
                    attendees = event.get('attendees', [])
                    participants = [
                        attendee.get('email', attendee.get('displayName', ''))
                        for attendee in attendees
                    ]
                    if 'organizer' in event:
                        organizer_email = event['organizer'].get('email', '')
                        if organizer_email and organizer_email not in participants:
                            participants.insert(0, organizer_email)
                    
                    # Build event summary
                    event_summary = f"Meeting: {title}"
                    if description:
                        event_summary += f"\n\n{description}"
                    
                    # Add event details to summary
                    if attendees:
                        event_summary += f"\n\nAttendees: {', '.join(participants)}"
                    
                    # Duration
                    duration_minutes = 0
                    if 'endTime' in event.get('start', {}):
                        try:
                            end_str = event.get('end', {}).get('dateTime') or event.get('end', {}).get('date')
                            if end_str:
                                end_time = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                                duration_minutes = int((end_time - event_time).total_seconds() / 60)
                        except:
                            pass
                    
                    # Create NormalizedInput
                    results.append(NormalizedInput(
                        source_type="calendar",
                        external_message_id=event_id,
                        timestamp=event_time,
                        participants=participants if participants else ["organizer"],
                        content_type="text",
                        raw_content=event_summary,
                        metadata={
                            "title": title,
                            "event_id": event_id,
                            "attendee_count": len(attendees),
                            "duration_minutes": duration_minutes,
                            "origin": "calendar",
                            "is_recurring": "recurringEventId" in event,
                            "location": event.get('location', ''),
                            "status": event.get('status', 'confirmed')
                        },
                        media=None
                    ))
                    
                    logger.debug(f"Calendar: Processed event '{title}'")
                
                except Exception as e:
                    logger.error(f"Calendar: Error processing event {event.get('id')}: {e}")
                    continue
            
            logger.info(f"Calendar: Successfully processed {len(results)} items")
            return results
        
        except HttpError as e:
            logger.error(f"Calendar: API error: {e}")
            return results
        except Exception as e:
            logger.error(f"Calendar: Unexpected error: {e}")
            return results
