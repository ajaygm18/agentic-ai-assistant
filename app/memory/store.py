from __future__ import annotations

from pathlib import Path
from threading import RLock
from urllib.parse import quote, unquote

from app.core.config import get_settings
from app.mcp.contexts import ConversationTurn, MemoryContext
from app.memory.base import BaseMemoryStore, SessionRecord


class FileSessionStore(BaseMemoryStore):
    def __init__(self, base_dir: Path | None = None) -> None:
        settings = get_settings()
        self._base_dir = Path(base_dir or settings.session_store_directory)
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()

    def get_session(self, session_id: str) -> SessionRecord:
        with self._lock:
            session = self._read_session(session_id)
            if session is None:
                session = SessionRecord(session_id=session_id)
                self._write_session(session)
            return session

    def append_turn(self, session_id: str, turn: ConversationTurn) -> SessionRecord:
        with self._lock:
            session = self.get_session(session_id)
            session.turns.append(turn)
            session.updated_at = turn.created_at
            self._write_session(session)
            return session

    def build_context(self, session_id: str, window_size: int) -> MemoryContext:
        session = self.get_session(session_id)
        turns = session.turns[-window_size:] if window_size > 0 else session.turns
        summary = " | ".join(f"{turn.role}: {turn.content[:120]}" for turn in turns[-4:]) if turns else None
        return MemoryContext(
            session_id=session_id,
            turns=list(turns),
            summary=summary,
            updated_at=session.updated_at,
        )

    def list_sessions(self) -> list[str]:
        with self._lock:
            sessions: list[str] = []
            for path in sorted(self._base_dir.glob("*.json")):
                sessions.append(unquote(path.stem))
            return sessions

    def _session_path(self, session_id: str) -> Path:
        return self._base_dir / f"{quote(session_id, safe='')}.json"

    def _read_session(self, session_id: str) -> SessionRecord | None:
        path = self._session_path(session_id)
        if not path.exists():
            return None
        return SessionRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def _write_session(self, session: SessionRecord) -> None:
        path = self._session_path(session.session_id)
        temp_path = path.with_suffix(".json.tmp")
        temp_path.write_text(session.model_dump_json(indent=2), encoding="utf-8")
        temp_path.replace(path)
