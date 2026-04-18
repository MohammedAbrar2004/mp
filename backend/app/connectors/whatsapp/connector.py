from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from models.normalized_input import NormalizedInput, PendingMedia


def _parse_timestamp(ts: Any) -> datetime:
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc)
    except (ValueError, TypeError, OSError):
        return datetime.now(timezone.utc)


def _jid_to_phone(jid: str) -> str:
    return "+" + jid.split("@")[0].split(":")[0]


def _is_group(jid: str) -> bool:
    return jid.endswith("@g.us")


class WhatsAppConnector:
    def handle_message(self, message: Dict[str, Any]) -> Optional[NormalizedInput]:
        try:
            key = message.get("key", {})
            remote_jid: str = key.get("remoteJid", "")
            message_id: str = key.get("id", "")

            if not remote_jid or not message_id:
                return None

            msg_body = message.get("message", {})
            if not msg_body:
                return None

            content = ""
            message_type = "text"
            media: List[PendingMedia] = []
            event_time = _parse_timestamp(message.get("messageTimestamp", 0))

            if "conversation" in msg_body:
                content = msg_body["conversation"]
                message_type = "text"

            elif "extendedTextMessage" in msg_body:
                content = msg_body["extendedTextMessage"].get("text", "")
                message_type = "text"

            elif "documentWithCaptionMessage" in msg_body:
                # DOCX and other documents sent with a caption arrive in this wrapper
                inner = msg_body["documentWithCaptionMessage"].get("message", {})
                doc = inner.get("documentMessage", {})
                content = inner.get("caption", "") or doc.get("caption", "")
                message_type = "document"
                file_bytes: Optional[bytes] = message.get("_file_bytes")
                if file_bytes:
                    media.append(PendingMedia(
                        raw_bytes=file_bytes,
                        original_filename=doc.get("fileName", "document"),
                        mime_type=doc.get("mimetype", "application/octet-stream"),
                        captured_at=event_time,
                    ))

            elif "documentMessage" in msg_body:
                doc = msg_body["documentMessage"]
                content = doc.get("caption", "")
                message_type = "document"
                file_bytes = message.get("_file_bytes")
                if file_bytes:
                    media.append(PendingMedia(
                        raw_bytes=file_bytes,
                        original_filename=doc.get("fileName", "document"),
                        mime_type=doc.get("mimetype", "application/octet-stream"),
                        captured_at=event_time,
                    ))

            elif "audioMessage" in msg_body:
                audio = msg_body["audioMessage"]
                message_type = "audio"
                file_bytes = message.get("_file_bytes")
                if file_bytes:
                    media.append(PendingMedia(
                        raw_bytes=file_bytes,
                        original_filename=f"voice_note_{message_id}.ogg",
                        mime_type=audio.get("mimetype", "audio/ogg"),
                        captured_at=event_time,
                    ))

            else:
                return None

            is_group = _is_group(remote_jid)
            if is_group:
                sender_jid = message.get("participant") or key.get("participant", "")
                sender = _jid_to_phone(sender_jid) if sender_jid else "unknown"
            else:
                sender = _jid_to_phone(remote_jid)

            participants = [sender] if sender != "unknown" else []

            if message_type == "document":
                content_type = "document"
            elif message_type == "audio":
                content_type = "audio"
            else:
                content_type = "text"

            metadata: Dict[str, Any] = {
                "chat_id": remote_jid,
                "is_group": is_group,
                "sender": sender,
                "message_type": message_type,
            }
            if content:
                metadata["caption"] = content

            return NormalizedInput(
                source_type="whatsapp",
                external_id=message_id,
                content=content,
                content_type=content_type,
                event_time=event_time,
                participants=participants,
                metadata=metadata,
                media=media,
            )

        except Exception as e:
            print(f"[WhatsAppConnector] Failed to parse message: {e}")
            return None
