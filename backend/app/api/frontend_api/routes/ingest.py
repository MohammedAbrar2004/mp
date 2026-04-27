import os
import tempfile
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, UploadFile, File, HTTPException, BackgroundTasks

from app.api.frontend_api.dependencies import get_db
from app.connectors.manual.connector import ManualConnector
from models.normalized_input import PendingMedia
from pipelines.ingestion_pipeline import process

router = APIRouter(prefix="/ingest", tags=["ingest"])

connector = ManualConnector()


def _run_full_pipeline():
    from app.preprocessing.orchestrator.preprocessing_pipeline import run_preprocessing
    from app.semantic.processor import run_semantic
    run_preprocessing()
    run_semantic()


@router.post("/text")
async def ingest_text(
    background_tasks: BackgroundTasks,
    content: str = Form(...),
    title: str = Form(""),
    source_label: str = Form("manual"),
    tags: str = Form(""),
    people: str = Form(""),
    conn=Depends(get_db),
):
    if not content.strip():
        raise HTTPException(status_code=400, detail="content is required")

    participants = [p.strip() for p in people.split(",") if p.strip()] or ["User"]
    tags_list = [t.strip() for t in tags.split(",") if t.strip()]
    metadata = {"source": source_label, "title": title, "tags": tags_list}

    normalized = connector.create_input(
        content=content,
        participants=participants,
        metadata=metadata,
        media=[],
    )
    process([normalized])
    background_tasks.add_task(_run_full_pipeline)
    return {"status": "ok", "chunk_id": normalized.external_id}


@router.post("/voice")
async def ingest_voice(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(""),
    tags: str = Form(""),
    conn=Depends(get_db),
):
    raw = await file.read()
    mime = file.content_type or "audio/webm"
    if not mime.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File must be an audio file")

    pending = PendingMedia(
        raw_bytes=raw,
        original_filename=file.filename or "voice_note.webm",
        mime_type=mime,
        captured_at=datetime.now(timezone.utc),
    )

    tags_list = [t.strip() for t in tags.split(",") if t.strip()]
    metadata = {"title": title, "tags": tags_list}

    normalized = connector.create_input(
        content="",
        participants=["User"],
        metadata=metadata,
        media=[pending],
    )
    process([normalized])
    background_tasks.add_task(_run_full_pipeline)
    return {"status": "ok", "chunk_id": normalized.external_id}


@router.post("/document")
async def ingest_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(""),
    author: str = Form(""),
    tags: str = Form(""),
    description: str = Form(""),
    conn=Depends(get_db),
):
    raw = await file.read()
    mime = file.content_type or "application/octet-stream"

    allowed_mimes = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    filename = file.filename or ""
    if mime not in allowed_mimes and not filename.lower().endswith((".pdf", ".doc", ".docx")):
        raise HTTPException(status_code=400, detail="File must be a PDF or Word document")

    if "pdf" in filename.lower() or mime == "application/pdf":
        actual_mime = "application/pdf"
    else:
        actual_mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    pending = PendingMedia(
        raw_bytes=raw,
        original_filename=filename,
        mime_type=actual_mime,
        captured_at=datetime.now(timezone.utc),
    )

    tags_list = [t.strip() for t in tags.split(",") if t.strip()]
    metadata = {
        "title": title,
        "author": author,
        "description": description,
        "tags": tags_list,
    }

    normalized = connector.create_input(
        content=description,
        participants=["User"],
        metadata=metadata,
        media=[pending],
    )
    process([normalized])
    background_tasks.add_task(_run_full_pipeline)
    return {"status": "ok", "chunk_id": normalized.external_id}
