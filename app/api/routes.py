from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.core.container import (
    get_assistant_service,
    get_ingestion_service,
    get_mcp_client,
    get_memory_store,
    get_vector_store_manager,
)
from app.models.api import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    SessionResponse,
)


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    vector_store_manager = get_vector_store_manager()
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        llm_base_url=settings.llm_base_url,
        llm_model=settings.llm_model,
        embedding_model=settings.embedding_model,
        vector_store_ready=vector_store_manager.has_index(),
        indexed_chunks=vector_store_manager.count_chunks(),
    )


@router.post("/ingest", response_model=IngestResponse)
def ingest(request: IngestRequest) -> IngestResponse:
    service = get_ingestion_service()
    try:
        doc_dir = Path(request.doc_dir) if request.doc_dir else None
        result = service.ingest(doc_dir=doc_dir)
        return IngestResponse(**result)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    service = get_assistant_service()
    try:
        return service.chat(session_id=request.session_id, user_message=request.user_message)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Chat request failed: {exc}") from exc


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str) -> SessionResponse:
    try:
        content = get_mcp_client().read_resource(f"session://{session_id}")
        payload = json.loads(content)
        return SessionResponse(
            session_id=payload["session_id"],
            turn_count=len(payload.get("turns", [])),
            updated_at=payload.get("updated_at"),
            turns=payload.get("turns", []),
        )
    except Exception:
        session = get_memory_store().get_session(session_id)
        return SessionResponse(
            session_id=session_id,
            turn_count=len(session.turns),
            updated_at=session.updated_at,
            turns=session.turns,
        )
