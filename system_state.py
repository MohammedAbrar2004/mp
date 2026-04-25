# EchoMind — system configuration
# Pattern: Ingestion → wait → Preprocessing → wait → repeat

WAIT_AFTER_INGESTION_MINS    = 15   # pause between ingestion finishing and preprocessing starting
WAIT_AFTER_PREPROCESSING_MINS = 15  # pause between preprocessing finishing and next ingestion
