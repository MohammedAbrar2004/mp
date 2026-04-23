-- Preprocessing Layer — DB column additions
-- Safe to run multiple times (uses IF NOT EXISTS / column existence checks).

-- memory_chunks: cleaned content + flags
ALTER TABLE memory_chunks
    ADD COLUMN IF NOT EXISTS content      TEXT,
    ADD COLUMN IF NOT EXISTS is_cleaned   BOOLEAN NOT NULL DEFAULT FALSE;

-- media_files: cleaned content + flags
ALTER TABLE media_files
    ADD COLUMN IF NOT EXISTS cleaned_content  TEXT,
    ADD COLUMN IF NOT EXISTS is_cleaned       BOOLEAN NOT NULL DEFAULT FALSE;
