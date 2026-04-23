"""
PDF Processor — Media Processing Service

Purpose:
    Extract raw text from PDF files stored on disk.
    Supports both text-based PDFs (pypdf) and scanned/image PDFs (OCR via Tesseract).

Input:
    local_path (str): Absolute path to the PDF file on disk.
    mime_type  (str): MIME type of the file (expected: application/pdf).

Output:
    extracted_content (str): Raw extracted text from the PDF.
                             Returns None on failure.

Behavior:
    - Primary: pypdf text extraction.
    - Fallback: pdf2image + pytesseract OCR when pypdf yields < 50 chars.
    - Extracts raw text only. Does NOT clean, normalize, or modify content.
    - Does NOT write to the database.
    - Does NOT modify memory_chunks.
    - Idempotent: safe to call multiple times on the same file.
    - On failure: logs error and returns None (caller handles retry).

Trigger Condition (enforced by orchestrator):
    media_files.extracted_content IS NULL
    AND mime_type = 'application/pdf'
"""

import logging
import os
from typing import Optional

from pypdf import PdfReader

logger = logging.getLogger("echomind.preprocessing.media.pdf")

_OCR_THRESHOLD = 50


def _extract_with_pypdf(local_path: str) -> Optional[str]:
    reader = PdfReader(local_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages).strip()
    return text if text else None


def _extract_with_ocr(local_path: str) -> Optional[str]:
    from pdf2image import convert_from_path
    import pytesseract

    images = convert_from_path(local_path)
    ocr_text = ""
    for img in images:
        ocr_text += pytesseract.image_to_string(img)
    text = ocr_text.strip()
    logger.info("OCR extracted length: %d", len(text))
    return text if text else None


def extract_text_from_pdf(local_path: str, mime_type: str) -> Optional[str]:
    """
    Extract raw text from a PDF file.

    Tries pypdf first; falls back to Tesseract OCR for scanned PDFs.

    Args:
        local_path: Absolute path to the PDF file on disk.
        mime_type:  MIME type of the file (should be 'application/pdf').

    Returns:
        Raw extracted text as a string, or None if extraction fails.
    """
    if not os.path.exists(local_path):
        logger.error("PDF file not found: '%s'", local_path)
        return None

    # Primary: pypdf
    try:
        logger.info("Using pypdf extraction for '%s'", local_path)
        text = _extract_with_pypdf(local_path)
        if text and len(text.strip()) >= _OCR_THRESHOLD:
            logger.info("pypdf extraction succeeded (%d chars)", len(text))
            return text
        logger.warning(
            "pypdf returned too little text (%d chars) — falling back to OCR",
            len(text.strip()) if text else 0,
        )
    except Exception as e:
        logger.error("pypdf extraction failed for '%s': %s", local_path, e)

    # Fallback: OCR
    try:
        logger.warning("Fallback to OCR for '%s'", local_path)
        return _extract_with_ocr(local_path)
    except Exception as e:
        logger.error("OCR extraction failed for '%s': %s", local_path, e)
        return None
