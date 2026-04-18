"""
Google Meet connector for EchoMind.
Fetches past Google Meet recordings and transcripts via Google Drive API.
Normalizes to NormalizedInput format.
"""

import logging
import pickle
from datetime import datetime, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.connectors.base_connector import BaseConnector
from models.normalized_input import NormalizedInput

logger = logging.getLogger("EchoMind.GMeet")


class GMeetConnector(BaseConnector):
    """Google Meet data connector via Google Drive API for recordings."""
    
    # Drive API scope - read-only
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    # How many days back to search for Meet recordings
    DAYS_LOOKBACK = 30
    
    def __init__(self):
        """Initialize GMeet connector with OAuth credentials."""
        super().__init__()
        self.connector_dir = Path(__file__).parent
        self.credentials_path = self.connector_dir.parent / 'gmail' / 'credentials.json'
        self.token_path = self.connector_dir / 'token.json'
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Drive API using OAuth."""
        creds = None
        
        # Load existing token if available
        if self.token_path.exists():
            with open(self.token_path, 'rb') as token_file:
                creds = pickle.load(token_file)
                logger.info("GMeet: Loaded cached token")
        
        # Refresh or request new credentials
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("GMeet: Token refreshed")
            except Exception as e:
                logger.warning(f"GMeet: Token refresh failed: {e}")
                creds = None
        
        if not creds or not creds.valid:
            if not self.credentials_path.exists():
                raise FileNotFoundError(
                    f"GMeet credentials.json not found at {self.credentials_path}. "
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
                logger.info("GMeet: New token generated and saved")
            except Exception as e:
                raise RuntimeError(f"GMeet OAuth authentication failed: {e}")
        
        self.service = build('drive', 'v3', credentials=creds)
        logger.info("GMeet: Service initialized")
    
    def fetch_data(self) -> list[NormalizedInput]:
        """
        Fetch Google Meet recordings from Google Drive.
        Search for files created by Google Meet (usually in a Meet folder).
        Extract metadata and create NormalizedInput objects.
        """
        results = []
        
        if not self.service:
            logger.error("GMeet: Not authenticated")
            return results
        
        try:
            # Calculate lookback window
            lookback_date = (datetime.utcnow() - timedelta(days=self.DAYS_LOOKBACK)).isoformat() + 'Z'
            
            # Search for Google Meet recordings
            # Typically found in 'Google Meet Recordings' folder or created by Google Meet
            query = (
                f"(name contains 'Meet' or name contains 'meeting' or "
                f"'root' in parents) and "
                f"createdTime > '{lookback_date}' and "
                f"trashed=false"
            )
            
            files = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, createdTime, modifiedTime, description, owners, webViewLink, mimeType)',
                pageSize=20,
                orderBy='createdTime desc'
            ).execute().get('files', [])
            
            logger.info(f"GMeet: Found {len(files)} potential recordings")
            
            for file in files:
                try:
                    file_id = file.get('id', '')
                    file_name = file.get('name', '[No Title]')
                    created_time_str = file.get('createdTime', '')
                    description = file.get('description', '')
                    mime_type = file.get('mimeType', '')
                    
                    # Parse file creation time
                    try:
                        file_time = datetime.fromisoformat(created_time_str.replace('Z', '+00:00'))
                    except:
                        file_time = datetime.now()
                    
                    # Extract owner/creator
                    owners = file.get('owners', [])
                    participants = [
                        owner.get('emailAddress', owner.get('displayName', ''))
                        for owner in owners
                    ]
                    
                    # Build meeting summary
                    meeting_summary = f"Google Meet Recording: {file_name}"
                    
                    if description:
                        meeting_summary += f"\n\nDescription: {description}"
                    
                    # Basic content type detection
                    if 'video' in mime_type:
                        content_type = "text"  # Metadata about video
                    else:
                        content_type = "document"
                    
                    # Create NormalizedInput
                    results.append(NormalizedInput(
                        source_type="gmeet",
                        external_message_id=file_id,
                        timestamp=file_time,
                        participants=participants if participants else ["unknown"],
                        content_type=content_type,
                        raw_content=meeting_summary,
                        metadata={
                            "file_id": file_id,
                            "file_name": file_name,
                            "mime_type": mime_type,
                            "origin": "gmeet_recording",
                            "recording_title": file_name,
                            "web_link": file.get('webViewLink', '')
                        },
                        media=None
                    ))
                    
                    logger.debug(f"GMeet: Processed recording '{file_name}'")
                
                except Exception as e:
                    logger.error(f"GMeet: Error processing file {file.get('id')}: {e}")
                    continue
            
            logger.info(f"GMeet: Successfully processed {len(results)} items")
            return results
        
        except HttpError as e:
            logger.error(f"GMeet: API error: {e}")
            return results
        except Exception as e:
            logger.error(f"GMeet: Unexpected error: {e}")
            return results
