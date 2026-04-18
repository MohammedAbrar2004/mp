"""
FastAPI receiver for EchoMind.
Accepts pushed data from Node.js microservices and triggers ingestion.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import logging

from app.connectors.whatsapp.whatsapp_connector import WhatsAppConnector
from pipelines.ingestion_pipeline import run_ingestion_for_items

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EchoMind.Receiver")

app = FastAPI(title="EchoMind Receiver", version="1.0.0")

class WhatsAppMessage(BaseModel):
    chat_name: str
    message_id: str
    timestamp: str
    sender: str
    message: str
    is_group: bool
    has_media: bool = False
    media_data: str | None = None        # base64 string
    media_mime_type: str | None = None
    media_filename: str | None = None

class WhatsAppPayload(BaseModel):
    messages: List[WhatsAppMessage]


@app.get("/health")
def health():
    return {"status": "ok", "service": "EchoMind Receiver"}


@app.post("/ingest/whatsapp")
async def ingest_whatsapp(payload: WhatsAppPayload):
    if not payload.messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    logger.info(f"[Receiver] Received {len(payload.messages)} WhatsApp messages")

    try:
        connector = WhatsAppConnector()
        normalized = connector.fetch_from_push([m.model_dump() for m in payload.messages])

        inserted, duplicates, errors = run_ingestion_for_items(normalized, "whatsapp")

        return JSONResponse(
            status_code=200,
            content={
                "status": "ok",
                "received": len(payload.messages),
                "inserted": inserted,
                "duplicates": duplicates,
                "errors": errors,
            },
        )

    except Exception as e:
        logger.error(f"[Receiver] Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    from dotenv import load_dotenv
    load_dotenv()

    host = os.getenv("RECEIVER_HOST", "127.0.0.1")
    port = int(os.getenv("RECEIVER_PORT", "8000"))

    uvicorn.run("app.api.receiver:app", host=host, port=port, reload=False)
