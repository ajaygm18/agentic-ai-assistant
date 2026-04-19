from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from app.mcp.contexts import ConversationTurn, MemoryContext


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SessionRecord(BaseModel):
    session_id: str
    turns: list[ConversationTurn] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class BaseMemoryStore(ABC):
    @abstractmethod
    def get_session(self, session_id: str) -> SessionRecord:
        raise NotImplementedError

    @abstractmethod
    def append_turn(self, session_id: str, turn: ConversationTurn) -> SessionRecord:
        raise NotImplementedError

    @abstractmethod
    def build_context(self, session_id: str, window_size: int) -> MemoryContext:
        raise NotImplementedError

    @abstractmethod
    def list_sessions(self) -> list[str]:
        raise NotImplementedError
