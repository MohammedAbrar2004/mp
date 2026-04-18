"""
Gmail connector for EchoMind.
Fetches real emails via Gmail API with OAuth authentication.
Extracts body text + attachments, normalizes to NormalizedInput format.
"""

import os
import pickle
import base64
import json
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

try:
    from bs4 import BeautifulSoup
    HAS_BEAUTIFULSOUP = True
except ImportError:
    HAS_BEAUTIFULSOUP = False

from app.connectors.base_connector import BaseConnector
from app.services.media_service import MediaService
from models.normalized_input import NormalizedInput

logger = logging.getLogger("EchoMind.Gmail")


class GmailConnector(BaseConnector):
    """Gmail data connector with OAuth authentication and attachment handling."""
    
    # Gmail API scope - needs both reading and attachment modification
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
    
    # Supported attachment MIME types
    SUPPORTED_ATTACHMENTS = {
        'application/pdf': 'document',
        'application/msword': 'document',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'document',
        'application/vnd.ms-excel': 'document',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'document',
        'image/jpeg': 'image',
        'image/png': 'image',
        'image/webp': 'image',
        'audio/mpeg': 'audio',
        'audio/ogg': 'audio',
        'audio/wav': 'audio',
    }
    
    def __init__(self):
        """Initialize Gmail connector with OAuth credentials and MediaService."""
        super().__init__()
        self.connector_dir = Path(__file__).parent
        self.credentials_path = self.connector_dir / 'credentials.json'
        self.token_path = self.connector_dir / 'token.json'
        self.service = None
        self.media_service = MediaService()
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Gmail API using OAuth."""
        creds = None
        
        # Load existing token if available
        if self.token_path.exists():
            with open(self.token_path, 'rb') as token_file:
                creds = pickle.load(token_file)
                logger.info("Gmail: Loaded cached token")
        
        # Refresh or request new credentials
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("Gmail: Token refreshed")
            except Exception as e:
                logger.warning(f"Gmail: Token refresh failed: {e}")
                creds = None
        
        if not creds or not creds.valid:
            if not self.credentials_path.exists():
                raise FileNotFoundError(
                    f"Gmail credentials.json not found at {self.credentials_path}. "
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
                logger.info("Gmail: New token generated and saved")
            except Exception as e:
                raise RuntimeError(f"Gmail OAuth authentication failed: {e}")
        
        self.service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail: Service initialized")
    
    def fetch_data(self) -> list[NormalizedInput]:
        """
        Fetch unread emails from Gmail inbox.
        Extract body text + attachments, create NormalizedInput objects.
        Mark emails as read after successful processing.
        """
        results = []
        
        if not self.service:
            logger.error("Gmail: Not authenticated")
            return results
        
        try:
            # Fetch unread messages from inbox
            messages = self.service.users().messages().list(
                userId='me',
                q='is:unread in:inbox',
                maxResults=10
            ).execute().get('messages', [])
            
            logger.info(f"Gmail: Found {len(messages)} unread emails")
            
            for message in messages:
                try:
                    # Get full message details
                    msg = self.service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    ).execute()
                    
                    # Extract headers
                    headers = msg['payload']['headers']
                    email_id = msg['id']
                    thread_id = msg['threadId']
                    
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
                    from_addr = next((h['value'] for h in headers if h['name'] == 'From'), '')
                    to_addr = next((h['value'] for h in headers if h['name'] == 'To'), '')
                    date_str = next((h['value'] for h in headers if h['name'] == 'Date'), '')
                    
                    # Parse email date
                    try:
                        email_date = datetime.fromisoformat(
                            date_str.replace(' GMT', '').replace(' +0000', '').replace(' -0000', '')
                        )
                        if email_date.tzinfo is None:
                            email_date = email_date.replace(tzinfo=None)
                    except:
                        email_date = datetime.now()
                    
                    # Extract participants
                    participants = list(set(
                        [from_addr] + [to_addr] 
                        if to_addr else [from_addr]
                    ))
                    participants = [p.strip() for p in participants if p.strip()]
                    
                    # Extract body text
                    body_text = self._extract_body(msg['payload'])
                    
                    # Extract attachments
                    attachments = self._extract_attachments(email_id, msg['payload'])
                    
                    # Create NormalizedInput for the email body
                    if body_text.strip():
                        results.append(NormalizedInput(
                            source_type="gmail",
                            external_message_id=f"{email_id}_body",
                            timestamp=email_date,
                            participants=participants,
                            content_type="email",
                            raw_content=body_text,
                            metadata={
                                "subject": subject,
                                "email_id": email_id,
                                "thread_id": thread_id,
                                "origin": "gmail",
                                "attachment_count": len(attachments)
                            },
                            media=attachments if attachments else None
                        ))
                    
                    # Mark email as read
                    try:
                        self.service.users().messages().modify(
                            userId='me',
                            id=email_id,
                            body={'removeLabelIds': ['UNREAD']}
                        ).execute()
                        logger.debug(f"Gmail: Marked email {email_id} as read")
                    except Exception as e:
                        logger.warning(f"Gmail: Failed to mark email as read: {e}")
                
                except Exception as e:
                    logger.error(f"Gmail: Error processing email {message['id']}: {e}")
                    continue
            
            logger.info(f"Gmail: Successfully processed {len(results)} items")
            return results
        
        except HttpError as e:
            logger.error(f"Gmail: API error: {e}")
            return results
        except Exception as e:
            logger.error(f"Gmail: Unexpected error: {e}")
            return results
    
    def _extract_body(self, payload: dict) -> str:
        """Extract email body from payload, preferring plain text."""
        body = ""
        
        # Check for direct body (simple emails)
        if 'body' in payload and payload['body'].get('data'):
            try:
                body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
                return body
            except:
                pass
        
        # Check for parts (multipart emails)
        if 'parts' in payload:
            text_body = ""
            html_body = ""
            
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')
                
                if mime_type == 'text/plain' and part.get('body', {}).get('data'):
                    try:
                        text_body = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8')
                    except:
                        pass
                
                elif mime_type == 'text/html' and part.get('body', {}).get('data'):
                    try:
                        html_body = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8')
                    except:
                        pass
                
                # Recursively check nested parts
                elif mime_type.startswith('multipart/'):
                    nested = self._extract_body(part)
                    if nested:
                        body = nested
            
            # Prefer plain text, fall back to HTML stripped
            if text_body:
                return text_body
            elif html_body:
                return self._strip_html(html_body)
        
        return body
    
    def _strip_html(self, html: str) -> str:
        """Strip HTML tags and decode entities using BeautifulSoup if available."""
        if HAS_BEAUTIFULSOUP:
            try:
                soup = BeautifulSoup(html, 'html.parser')
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                # Get text
                text = soup.get_text()
                # Break into lines and remove leading/trailing space on each
                lines = (line.strip() for line in text.splitlines())
                # Break multi-headlines into a line each
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                # Drop blank lines
                text = '\n'.join(chunk for chunk in chunks if chunk)
                return text
            except Exception as e:
                logger.warning(f"Gmail: BeautifulSoup parsing failed: {e}, falling back to regex")
        
        # Fallback regex-based HTML stripping
        # Remove style and script tags
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        
        # Decode HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&quot;', '"')
        text = text.replace('&apos;', "'")
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&br;', '\n')
        text = text.replace('<br>', '\n')
        text = text.replace('<br/>', '\n')
        text = text.replace('<br />', '\n')
        
        # Clean up extra whitespace
        text = re.sub(r'\n\s*\n', '\n', text)
        
        return text
    
    def _extract_attachments(self, email_id: str, payload: dict) -> list:
        """
        Extract attachments from email payload and save using MediaService.
        
        Args:
            email_id: Gmail message ID
            payload: Email payload structure
            
        Returns:
            List of MediaObject instances
        """
        attachments = []
        
        def process_parts(parts):
            for part in parts:
                if part.get('filename'):
                    mime_type = part.get('mimeType', '')
                    filename = part.get('filename', 'attachment')
                    
                    # Check if this is a supported attachment type
                    if mime_type not in self.SUPPORTED_ATTACHMENTS:
                        logger.debug(f"Gmail: Skipping unsupported attachment type {mime_type}: {filename}")
                        continue
                    
                    try:
                        # Get attachment data
                        if 'data' in part.get('body', {}):
                            data = part['body']['data']
                        else:
                            # For larger attachments, need to fetch separately
                            attachment_data = self.service.users().messages().attachments().get(
                                userId='me',
                                messageId=email_id,
                                id=part['body']['attachmentId']
                            ).execute()
                            data = attachment_data.get('data', '')
                        
                        if not data:
                            logger.warning(f"Gmail: Attachment {filename} has no data")
                            continue
                        
                        # Decode base64
                        try:
                            file_bytes = base64.urlsafe_b64decode(data)
                        except Exception as e:
                            logger.error(f"Gmail: Failed to decode attachment {filename}: {e}")
                            continue
                        
                        # Save via MediaService
                        try:
                            media_obj = self.media_service.save(
                                raw_bytes=file_bytes,
                                original_filename=filename,
                                mime_type=mime_type,
                                source_type="gmail",
                                captured_at=datetime.now()
                            )
                            attachments.append(media_obj)
                            logger.info(f"Gmail: Saved attachment {filename} ({len(file_bytes)} bytes)")
                        except ValueError as e:
                            logger.warning(f"Gmail: Unsupported file type for {filename}: {e}")
                        except Exception as e:
                            logger.error(f"Gmail: Failed to save attachment {filename}: {e}")
                    
                    except Exception as e:
                        logger.error(f"Gmail: Failed to process attachment {filename}: {e}")
                
                # Recursively process nested parts
                elif part.get('parts'):
                    process_parts(part['parts'])
        
        # Start recursion if there are parts
        if 'parts' in payload:
            process_parts(payload['parts'])
        
        return attachments
