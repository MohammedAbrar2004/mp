"""
FastAPI endpoint — receives raw Baileys message payloads from the Node.js
service, decodes media bytes, then hands off to the connector and pipeline.

Run from backend/:
    uvicorn app.api.whatsapp_receiver:app --host 127.0.0.1 --port 8000 --reload
"""
import base64
import logging

from fastapi import FastAPI, HTTPException, Request
from dotenv import load_dotenv

load_dotenv()

from app.connectors.whatsapp.connector import WhatsAppConnector
from pipelines.ingestion_pipeline import process

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("echomind.receiver")

app = FastAPI(title="EchoMind Receiver")
connector = WhatsAppConnector()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    try:
        message = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Decode base64 media → raw bytes so the connector can build PendingMedia
    b64 = message.pop("_file_bytes_b64", None)
    if b64:
        try:
            message["_file_bytes"] = base64.b64decode(b64)
        except Exception:
            logger.warning("Could not decode _file_bytes_b64 — media will be skipped")

    result = connector.handle_message(message)
    if result is None:
        return {"status": "skipped", "id": message.get("key", {}).get("id")}

    process([result])
    logger.info("Ingested %s", result.external_id)
    return {"status": "ok", "id": result.external_id}
