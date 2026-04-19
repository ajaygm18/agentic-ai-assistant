from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Agentic AI Assistant"
    app_env: str = "local"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    openai_api_key: str = "anti-api-local-token"
    llm_base_url: str = "http://localhost:8964/v1"
    llm_model: str = "gpt-5.4"
    planner_model: str = "claude-opus-4-6"
    llm_temperature: float = 0.2

    embedding_api_key: str | None = None
    embedding_base_url: str | None = None
    embedding_model: str = "text-embedding-3-small"

    docs_dir: Path = Field(default=Path("data/docs"))
    chroma_persist_directory: Path = Field(default=Path("data/chroma"))
    session_store_directory: Path = Field(default=Path("data/sessions"))
    collection_name: str = "assistant_knowledge_base"
    chunk_size: int = 900
    chunk_overlap: int = 150
    retriever_top_k: int = 4
    memory_window: int = 8
    tool_loop_limit: int = 4
    mcp_server_module: str = "app.mcp.server"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def resolve_paths(self) -> "Settings":
        if not self.embedding_base_url:
            self.embedding_base_url = self.llm_base_url
        if not self.docs_dir.is_absolute():
            self.docs_dir = PROJECT_ROOT / self.docs_dir
        if not self.chroma_persist_directory.is_absolute():
            self.chroma_persist_directory = PROJECT_ROOT / self.chroma_persist_directory
        if not self.session_store_directory.is_absolute():
            self.session_store_directory = PROJECT_ROOT / self.session_store_directory
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
