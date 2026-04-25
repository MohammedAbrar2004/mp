"""
Manual Ingestion API — EchoMind

Standalone FastAPI app for manually ingesting text and media files.

Run from backend/:
    uvicorn app.api.manual_receiver:app --host 127.0.0.1 --port 8001 --reload

Endpoints:
    GET  /health
    POST /ingest   (multipart/form-data)
        content  (str, optional)    — plain text to store
        file     (file, optional)   — PDF, DOCX, DOC, OGG, MP3, WAV, MP4

Supported MIME types (enforced by MediaService):
    application/pdf
    application/msword
    application/vnd.openxmlformats-officedocument.wordprocessingml.document
    audio/ogg  audio/mpeg  audio/mp4  audio/wav
"""
import logging
import os

from datetime import datetime, timezone
from fastapi import FastAPI, Form, File, HTTPException, UploadFile
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../../../.env"))

from models.normalized_input import PendingMedia
from app.connectors.manual.connector import ManualConnector
from pipelines.ingestion_pipeline import process

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("echomind.manual")

app = FastAPI(title="EchoMind Manual Ingestion")
connector = ManualConnector()

_OWNER = "Abrar Farooque"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest")
async def manual_ingest(
    content: str = Form(default=""),
    file: UploadFile = File(default=None),
):
    """
    Ingest a manual text entry and/or a media file into EchoMind.

    At least one of content or file must be provided.
    """
    if not content.strip() and file is None:
        raise HTTPException(status_code=400, detail="Provide text content or upload a file")

    media = []
    if file is not None:
        raw_bytes = await file.read()
        media.append(PendingMedia(
            raw_bytes=raw_bytes,
            original_filename=file.filename,
            mime_type=file.content_type,
            captured_at=datetime.now(timezone.utc),
        ))

    try:
        normalized = connector.create_input(
            content=content,
            participants=[_OWNER],
            metadata={"source": "manual"},
            media=media,
        )
        process([normalized])
    except ValueError as e:
        # Unsupported MIME type or validation error
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Manual ingestion failed: %s", e)
        raise HTTPException(status_code=500, detail="Ingestion failed — check server logs")

    logger.info(
        "POST /ingest → 200  chunk_id=%s  content_type=%s",
        normalized.external_id,
        normalized.content_type,
    )
    return {"status": "ok", "chunk_id": normalized.external_id}
