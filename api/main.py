"""FastAPI entrypoint for the Cred Banking Support Agent application.

Task 11 requirements:
- Exposes at least 2 HTTP endpoints (POST /ask, POST /add-document).
- Exposes 1 WebSocket endpoint (/ws/chat) for multi-turn chat handling client disconnects gracefully.
- Integrates Pydantic request/response models.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure zero telemetry and redirect localappdata to workspace folder to prevent WinError 5
_ROOT_DIR = Path(__file__).resolve().parent.parent
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_TRACING_ENABLED"] = "false"
os.environ["CI"] = "true"
os.environ["LOCALAPPDATA"] = str(_ROOT_DIR / ".appdata")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as http_router
from api.websocket import ws_router

app = FastAPI(
    title="Cred Banking & FinTech Domain Support Agent",
    description=(
        "Production-minded banking support agent backend powered by multi-agent orchestration, "
        "deterministic RAG retrieval, PII masking, injection guardrails, and structured logging."
    ),
    version="1.0.0",
)

# Enable CORS for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include HTTP and WebSocket routers
app.include_router(http_router, tags=["Banking Operations"])
app.include_router(ws_router, tags=["Real-Time Chat"])


@app.get("/health", tags=["Monitoring"])
async def health_check() -> dict[str, str]:
    """Service health probe."""
    return {
        "status": "HEALTHY",
        "service": "cred-banking-agent",
        "track": "Banking & FinTech (Cred)",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=False)

