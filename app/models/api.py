from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.mcp.contexts import ConversationTurn, ExecutionTraceItem, RouteType, SourceCitation


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Logical conversation session key.")
    user_message: str = Field(..., min_length=1, description="End-user input.")


class ChatResponse(BaseModel):
    session_id: str
    route: RouteType
    answer: str
    sources: list[SourceCitation] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    execution_summary: list[ExecutionTraceItem] = Field(default_factory=list)
    memory_turn_count: int
    session_updated_at: datetime | None = None


class IngestRequest(BaseModel):
    doc_dir: str | None = Field(
        default=None,
        description="Optional override path. Defaults to DOCS_DIR from configuration.",
    )


class IngestResponse(BaseModel):
    status: str
    documents_loaded: int
    chunks_created: int
    collection_name: str
    persist_directory: str


class HealthResponse(BaseModel):
    status: str
    app_name: str
    llm_base_url: str
    llm_model: str
    embedding_model: str
    vector_store_ready: bool
    indexed_chunks: int


class SessionResponse(BaseModel):
    session_id: str
    turn_count: int
    updated_at: datetime | None = None
    turns: list[ConversationTurn] = Field(default_factory=list)
