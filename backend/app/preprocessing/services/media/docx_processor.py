"""
DOCX Processor — Media Processing Service

Purpose:
    Extract raw text from DOCX files stored on disk.
    Extracts paragraphs, tables, headers, and footers.

Input:
    local_path (str): Absolute path to the DOCX file on disk.
    mime_type  (str): MIME type of the file (expected:
                      application/vnd.openxmlformats-officedocument
                      .wordprocessingml.document).

Output:
    extracted_content (str): Raw extracted text from the DOCX.
                             Returns None on failure.

Behavior:
    - Extracts raw text only. Does NOT clean, normalize, or modify content.
    - Does NOT write to the database.
    - Does NOT modify memory_chunks.
    - Idempotent: safe to call multiple times on the same file.
    - On failure: logs error and returns None (caller handles retry).
    - Uses only stdlib (zipfile + xml.etree.ElementTree) — no lxml dependency.

Trigger Condition (enforced by orchestrator):
    media_files.extracted_content IS NULL
    AND mime_type = 'application/vnd.openxmlformats-officedocument
                    .wordprocessingml.document'
"""

import logging
import os
import zipfile
import xml.etree.ElementTree as ET
from typing import Optional

logger = logging.getLogger("echomind.preprocessing.media.docx")

_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _para_text(para_elem) -> str:
    """Concatenate all w:t run texts within a single w:p element."""
    return "".join(t.text or "" for t in para_elem.iter(f"{{{_W}}}t")).strip()


def _extract_part_paragraphs(xml_bytes: bytes) -> list[str]:
    """Return non-empty paragraph texts from a Word XML part (header or footer)."""
    root = ET.fromstring(xml_bytes)
    return [line for para in root.iter(f"{{{_W}}}p") if (line := _para_text(para))]


def _extract_document(xml_bytes: bytes) -> tuple[list[str], list[str]]:
    """
    Parse word/document.xml and return (paragraph_lines, table_lines).
    Iterates direct children of <w:body> so paragraphs inside tables are
    captured only in table_lines, not duplicated in paragraph_lines.
    """
    root = ET.fromstring(xml_bytes)
    body = root.find(f"{{{_W}}}body")
    if body is None:
        return [], []

    para_lines: list[str] = []
    table_lines: list[str] = []

    for child in body:
        if child.tag == f"{{{_W}}}p":
            line = _para_text(child)
            if line:
                para_lines.append(line)
        elif child.tag == f"{{{_W}}}tbl":
            for row in child.iter(f"{{{_W}}}tr"):
                cells = []
                for cell in row.findall(f"{{{_W}}}tc"):
                    cell_text = " ".join(
                        _para_text(p) for p in cell.iter(f"{{{_W}}}p") if _para_text(p)
                    )
                    if cell_text:
                        cells.append(cell_text)
                if cells:
                    table_lines.append(" | ".join(cells))

    return para_lines, table_lines


def extract_text_from_docx(local_path: str, mime_type: str) -> Optional[str]:
    """
    Extract raw text from a DOCX file including paragraphs, tables,
    headers, and footers.

    Args:
        local_path: Absolute path to the DOCX file on disk.
        mime_type:  MIME type of the file.

    Returns:
        Structured extracted text as a string, or None if extraction fails.
    """
    if not os.path.exists(local_path):
        logger.error("DOCX file not found: '%s'", local_path)
        return None

    try:
        with zipfile.ZipFile(local_path) as zf:
            names = zf.namelist()
            parts: list[str] = []

            # Headers (word/header1.xml, word/header2.xml, ...)
            header_lines: list[str] = []
            for name in sorted(n for n in names if n.startswith("word/header")):
                header_lines.extend(_extract_part_paragraphs(zf.read(name)))
            if header_lines:
                parts.append("[HEADER]")
                parts.extend(header_lines)

            # Main body
            if "word/document.xml" in names:
                para_lines, table_lines = _extract_document(zf.read("word/document.xml"))
                if para_lines:
                    parts.append("[CONTENT]")
                    parts.extend(para_lines)
                if table_lines:
                    parts.append("[TABLE]")
                    parts.extend(table_lines)

            # Footers (word/footer1.xml, word/footer2.xml, ...)
            footer_lines: list[str] = []
            for name in sorted(n for n in names if n.startswith("word/footer")):
                footer_lines.extend(_extract_part_paragraphs(zf.read(name)))
            if footer_lines:
                parts.append("[FOOTER]")
                parts.extend(footer_lines)

        text = "\n".join(parts).strip()
        if not text:
            return None

        logger.info("Extracted DOCX text length: %d", len(text))
        return text

    except Exception as e:
        logger.error("DOCX extraction failed for '%s': %s", local_path, e)
        return None
