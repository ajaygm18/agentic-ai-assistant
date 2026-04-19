from __future__ import annotations

from pathlib import Path
from threading import RLock

from langchain_core.documents import Document
from langchain_chroma import Chroma

from app.core.config import get_settings
from app.services.llm import get_embeddings


class VectorStoreManager:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._vector_store: Chroma | None = None
        self._lock = RLock()

    def load(self) -> Chroma | None:
        with self._lock:
            if self._vector_store is not None:
                return self._vector_store

            persist_dir = self.settings.chroma_persist_directory
            if not persist_dir.exists():
                return None

            self._vector_store = Chroma(
                collection_name=self.settings.collection_name,
                persist_directory=str(persist_dir),
                embedding_function=get_embeddings(),
            )
            return self._vector_store

    def rebuild(self, documents: list[Document]) -> Chroma:
        if not documents:
            raise ValueError("No documents were provided for ingestion.")

        with self._lock:
            persist_dir = self.settings.chroma_persist_directory
            persist_dir.mkdir(parents=True, exist_ok=True)

            if self._vector_store is not None:
                try:
                    self._vector_store.delete_collection()
                except Exception:  # noqa: BLE001
                    pass
                self._vector_store = None
            else:
                try:
                    existing = Chroma(
                        collection_name=self.settings.collection_name,
                        persist_directory=str(persist_dir),
                        embedding_function=get_embeddings(),
                    )
                    existing.delete_collection()
                except Exception:  # noqa: BLE001
                    pass

            self._vector_store = Chroma.from_documents(
                documents=documents,
                embedding=get_embeddings(),
                persist_directory=str(persist_dir),
                collection_name=self.settings.collection_name,
            )
            return self._vector_store

    def has_index(self) -> bool:
        store = self.load()
        return bool(store and self.count_chunks() > 0)

    def count_chunks(self) -> int:
        store = self.load()
        if store is None:
            return 0
        return int(store._collection.count())

    @property
    def persist_directory(self) -> Path:
        return self.settings.chroma_persist_directory
