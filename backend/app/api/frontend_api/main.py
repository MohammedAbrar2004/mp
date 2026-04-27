from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.frontend_api.routes import (
    query,
    memory,
    ingest,
    relations,
    connectors,
    settings,
)

app = FastAPI(title="EchoMind Frontend API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router)
app.include_router(memory.router)
app.include_router(ingest.router)
app.include_router(relations.router)
app.include_router(connectors.router)
app.include_router(settings.router)


@app.get("/health")
def health():
    return {"status": "ok"}
