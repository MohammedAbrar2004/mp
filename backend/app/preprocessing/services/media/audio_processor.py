"""
Audio Processor — Media Processing Service

Purpose:
    Transcribe audio files (voice notes) stored on disk into English text
    using OpenAI Whisper (local inference).

Input:
    local_path (str): Absolute path to the audio file on disk.
    mime_type  (str): MIME type of the file (e.g. audio/ogg, audio/mpeg).

Output:
    extracted_content (str): English transcription of the audio.
                             Returns None on failure.

Behavior:
    - Uses whisper "base" model with task="translate" so all output is English,
      including Hindi and Hinglish recordings.
    - Produces raw transcription only. Does NOT clean or summarize output.
    - Does NOT write to the database.
    - Does NOT modify memory_chunks.
    - Idempotent: safe to call multiple times on the same file.
    - On failure: logs error and returns None (caller handles retry).

Trigger Condition (enforced by orchestrator):
    media_files.extracted_content IS NULL
    AND media_type = 'audio'
"""

import logging
import os

# os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\ffmpeg-8.1-essentials_build\bin"

logger = logging.getLogger("echomind.preprocessing.media.audio")

# Loaded once at module level to avoid reloading on every call
_whisper_model = None


def _get_model():
    global _whisper_model
    if _whisper_model is None:
        import whisper
        logger.info("Loading Whisper 'base' model...")
        _whisper_model = whisper.load_model("medium")
        logger.info("Whisper model loaded")
    return _whisper_model


def transcribe_audio(local_path: str, mime_type: str) -> str | None:
    """
    Transcribe an audio file to English text using Whisper.

    Supports English, Hindi, and Hinglish. task="translate" forces
    all output to English regardless of source language.

    Args:
        local_path: Absolute path to the audio file on disk.
        mime_type:  MIME type of the audio file.

    Returns:
        English transcription string, or None on failure.
    """
    if not os.path.exists(local_path):
        logger.error("Audio file not found: '%s'", local_path)
        return None

    try:
        model = _get_model()
        logger.info("Transcribing '%s'", local_path)
        result = model.transcribe(
            local_path, 
            task="translate", 
            fp16=False,
            language="en",
            temperature=0
          )  # Force English output)
        text = result["text"].strip()

        if not text:
            logger.warning("Whisper returned empty transcription for '%s'", local_path)
            return None

        logger.info("Transcription complete for '%s' (%d chars)", local_path, len(text))
        return text

    except Exception as e:
        logger.error("Transcription failed for '%s': %s", local_path, e)
        return None
