from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RouteType(str, Enum):
    DIRECT = "direct"
    RAG = "rag"
    TOOL = "tool"
    HYBRID = "hybrid"


class ConversationTurn(BaseModel):
    role: Literal["user", "assistant"] = Field(..., description="Conversation actor.")
    content: str = Field(..., description="Turn text.")
    created_at: datetime = Field(default_factory=utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryContext(BaseModel):
    session_id: str
    turns: list[ConversationTurn] = Field(default_factory=list)
    summary: str | None = None
    updated_at: datetime | None = None


class UserQueryContext(BaseModel):
    session_id: str
    user_message: str
    normalized_query: str
    received_at: datetime = Field(default_factory=utcnow)


class SourceCitation(BaseModel):
    source_id: str
    title: str
    source_path: str
    relevance_score: float | None = None
    excerpt: str | None = None


class RetrievedKnowledgeContext(BaseModel):
    query: str
    available: bool = False
    total_hits: int = 0
    citations: list[SourceCitation] = Field(default_factory=list)


class ToolResultContext(BaseModel):
    tool_name: str
    tool_input: dict[str, Any] = Field(default_factory=dict)
    status: Literal["completed", "failed"] = "completed"
    output: str
    called_at: datetime = Field(default_factory=utcnow)


class ExecutionTraceItem(BaseModel):
    stage: str
    message: str
    timestamp: datetime = Field(default_factory=utcnow)
    data: dict[str, Any] = Field(default_factory=dict)


class PlanStep(BaseModel):
    step_id: str
    title: str
    description: str
    requires_retrieval: bool = False
    allows_tools: bool = False


class RoutingDecision(BaseModel):
    route: RouteType
    rationale: list[str] = Field(default_factory=list)


class AgentExecutionState(BaseModel):
    session_id: str
    route: RouteType
    user_query: UserQueryContext
    memory: MemoryContext
    routing: RoutingDecision
    plan: list[PlanStep] = Field(default_factory=list)
    retrieved_knowledge: RetrievedKnowledgeContext | None = None
    tool_results: list[ToolResultContext] = Field(default_factory=list)
    trace: list[ExecutionTraceItem] = Field(default_factory=list)
    final_answer: str | None = None
