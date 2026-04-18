"""
WhatsApp connector for EchoMind.
Primary mode  : accepts pushed messages from Node.js microservice.
Fallback mode : reads from .txt export files (manual backfill).
"""

import base64
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from app.connectors.base_connector import BaseConnector
from app.services.media_service import MediaService
from models.normalized_input import NormalizedInput


class WhatsAppConnector(BaseConnector):

    WHATSAPP_FOLDER = "data/whatsapp"
    STATE_FILE = "data/whatsapp_state.json"

    def __init__(self):
        self.media_service = MediaService()

    def _generate_message_id(self, timestamp: str, sender: str, message: str) -> str:
        raw = f"{timestamp}_{sender}_{message}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def fetch_data(self) -> list[NormalizedInput]:
        return []

    def fetch_from_push(self, messages: list[dict]) -> list[NormalizedInput]:
        normalized = []

        for msg in messages:
            try:
                timestamp = datetime.fromisoformat(msg["timestamp"].replace("Z", "+00:00"))
                external_id = msg.get("message_id") or self._generate_message_id(
                    msg.get("timestamp", ""),
                    msg.get("sender", ""),
                    msg.get("message", "")
                )

                # Handle media if present
                media_objects = None
                metadata = {
                    "origin": "whatsapp_push",
                    "chat_name": msg.get("chat_name"),
                    "is_group": msg.get("is_group", False)
                }

                if msg.get("has_media") and msg.get("media_data") and msg.get("media_mime_type"):
                    try:
                        raw_bytes = base64.b64decode(msg["media_data"])
                        media_obj = self.media_service.save(
                            raw_bytes=raw_bytes,
                            original_filename=msg.get("media_filename") or f"whatsapp_{external_id}",
                            mime_type=msg["media_mime_type"],
                            source_type="whatsapp",
                            captured_at=timestamp
                        )
                        media_objects = [media_obj]
                        metadata["media_filename"] = msg.get("media_filename")
                        metadata["media_mime_type"] = msg["media_mime_type"]
                    except Exception as e:
                        print(f"[WhatsAppConnector] Failed to save media: {e}")

                # Determine content type
                mime = msg.get("media_mime_type", "")
                if mime.startswith("audio/"):
                    content_type = "audio"
                elif msg.get("has_media"):
                    content_type = "document"
                else:
                    content_type = "text"

                normalized.append(NormalizedInput(
                    source_type="whatsapp",
                    external_message_id=external_id,
                    timestamp=timestamp,
                    participants=[(msg.get("sender") or "unknown").lower()],
                    content_type=content_type,
                    raw_content=msg.get("message", ""),
                    metadata=metadata,
                    media=media_objects
                ))

            except Exception as e:
                print(f"[WhatsAppConnector] Skipping malformed message: {e}")
                continue

        return normalized

    def fetch_from_files(self) -> list[NormalizedInput]:
        all_messages = []

        if not os.path.exists(self.WHATSAPP_FOLDER):
            print(f"[WhatsAppConnector] Fallback folder not found: {self.WHATSAPP_FOLDER}")
            return all_messages

        last_hash = self._load_state()
        found_marker = last_hash is None
        last_processed_hash = None
        last_processed_timestamp = None

        txt_files = sorted(Path(self.WHATSAPP_FOLDER).glob("*.txt"))

        for file_path in txt_files:
            try:
                messages = self._parse_export_file(file_path)

                for msg in messages:
                    sender = msg.participants[0] if msg.participants else "unknown"
                    msg_hash = self._generate_message_id(
                        msg.timestamp.isoformat(), sender, msg.raw_content
                    )

                    if not found_marker:
                        if msg_hash == last_hash:
                            found_marker = True
                        continue

                    all_messages.append(msg)
                    last_processed_hash = msg_hash
                    last_processed_timestamp = msg.timestamp

            except Exception as e:
                print(f"[WhatsAppConnector] Error reading {file_path.name}: {e}")
                continue

        if last_processed_hash:
            self._save_state(last_processed_hash, last_processed_timestamp)

        return all_messages

    def _load_state(self) -> str | None:
        if not os.path.exists(self.STATE_FILE):
            return None
        try:
            with open(self.STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("last_message_hash")
        except Exception:
            return None

    def _save_state(self, message_hash: str, timestamp: datetime):
        try:
            os.makedirs(os.path.dirname(self.STATE_FILE), exist_ok=True)
            with open(self.STATE_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "last_message_hash": message_hash,
                    "last_timestamp": timestamp.isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"[WhatsAppConnector] Failed to save state: {e}")

    def _parse_export_file(self, file_path: Path) -> list[NormalizedInput]:
        messages = []

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                parsed = self._parse_line(line)
                if not parsed:
                    continue

                timestamp, sender, text = parsed

                if self._is_system_message(text):
                    continue

                external_id = self._generate_message_id(timestamp.isoformat(), sender, text)

                messages.append(NormalizedInput(
                    source_type="whatsapp",
                    external_message_id=external_id,
                    timestamp=timestamp,
                    participants=[sender.lower()],
                    content_type="text",
                    raw_content=text,
                    metadata={
                        "origin": "whatsapp_export",
                        "file_name": file_path.name
                    }
                ))

        return messages

    def _parse_line(self, line: str):
        try:
            line = line.strip("[]")
            if " - " not in line:
                return None

            ts_part, rest = line.split(" - ", 1)
            if ":" not in rest:
                return None

            sender, text = rest.split(":", 1)
            sender = sender.strip()
            text = text.strip()

            timestamp = None
            for fmt in ("%d/%m/%Y, %H:%M", "%m/%d/%y, %I:%M:%S %p", "%m/%d/%y, %H:%M"):
                try:
                    timestamp = datetime.strptime(ts_part.strip(), fmt)
                    break
                except ValueError:
                    continue

            if not timestamp:
                return None

            return (timestamp, sender, text)

        except Exception:
            return None

    def _is_system_message(self, message: str) -> bool:
        indicators = [
            "messages and calls are encrypted",
            "left", "joined", "created group", "added",
            "changed the subject", "removed",
            "changed this group's icon",
            "updated the message timer",
            "turned off disappearing messages",
            "this message was deleted",
            "media omitted"
        ]
        msg_lower = message.lower()
        return any(ind in msg_lower for ind in indicators)