"""
Media Service — Central Router for Media Processing

Purpose:
    Route a media file to the correct processor based on its MIME type
    and return raw extracted content (text or transcription).

Input:
    file_path (str): Absolute path to the media file on disk.
    mime_type (str): MIME type of the file.

Output:
    extracted_content (str): Raw extracted text.
                             Returns None if the MIME type is unsupported
                             or if the processor fails.

Routing:
    application/pdf                                                   → pdf_processor
    application/vnd.openxmlformats-officedocument.wordprocessingml.document → docx_processor
    audio/*                                                           → audio_processor

Behavior:
    - Does NOT clean or modify the extracted text.
    - Does NOT write to the database.
    - Does NOT modify memory_chunks.
    - Logs unsupported MIME types and returns None (orchestrator skips/retries).
    - Each underlying processor is called independently; failures are isolated.
"""

import logging

from .pdf_processor import extract_text_from_pdf
from .docx_processor import extract_text_from_docx
from .audio_processor import transcribe_audio

logger = logging.getLogger("echomind.preprocessing.media")

_MIME_PDF = "application/pdf"
_MIME_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def process_media_file(file_path: str, mime_type: str) -> str | None:
    """
    Route a media file to the correct processor and return raw extracted text.

    Args:
        file_path: Absolute path to the media file on disk.
        mime_type: MIME type string (e.g. 'application/pdf', 'audio/ogg').

    Returns:
        Raw extracted text as a string, or None if unsupported or on failure.
    """
    if mime_type == _MIME_PDF:
        return extract_text_from_pdf(file_path, mime_type)

    if mime_type == _MIME_DOCX:
        return extract_text_from_docx(file_path, mime_type)

    if mime_type.startswith("audio/"):
        return transcribe_audio(file_path, mime_type)

    logger.warning("Unsupported MIME type '%s' for file '%s' — skipping", mime_type, file_path)
    return None
