"""
Salience Service — Preprocessing Layer

Purpose:
    Assign an initial importance score (0.0–1.0) to each memory_chunk.
    This score controls whether a chunk is forwarded to the semantic layer.

Input:
    content       (str):  Cleaned text from memory_chunks.content.
    metadata      (dict): Chunk metadata (source, timestamps, participants, etc.).
    has_media     (bool): Whether the chunk has associated media_files rows.

Output:
    initial_salience (float): Importance score in range [0.0, 1.0].
                              Returns None on failure.

Behavior:
    Heuristics (initial implementation):
        - Content length: longer content → higher base score.
        - Keyword presence: action words, names, dates → boost.
        - Media presence: chunks with attachments → boost.
    - Does NOT write to the database directly.
    - Does NOT call other services.
    - Stateless and idempotent.
    - On failure: logs error and returns None (orchestrator handles retry).

Trigger Condition (enforced by orchestrator):
    content IS NOT NULL
    AND initial_salience IS NULL
"""


def compute_salience(
    content: str,
    metadata: dict,
    has_media: bool,
) -> float | None:
    """
    Compute an initial salience score for a memory_chunk.

    Args:
        content:   Cleaned text (memory_chunks.content).
        metadata:  Chunk metadata dict.
        has_media: True if the chunk has one or more linked media_files rows.

    Returns:
        Float score in [0.0, 1.0], or None if computation fails.
    """
    pass
