from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.core.config import get_settings
from app.rag.vectorstore import VectorStoreManager


TEXT_EXTENSIONS = {".md", ".txt", ".rst"}
PDF_EXTENSIONS = {".pdf"}
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | PDF_EXTENSIONS


class DocumentIngestionService:
    def __init__(self, vector_store_manager: VectorStoreManager) -> None:
        self.settings = get_settings()
        self.vector_store_manager = vector_store_manager

    def ingest(self, doc_dir: Path | None = None) -> dict[str, int | str]:
        target_dir = Path(doc_dir or self.settings.docs_dir)
        documents = self._load_documents(target_dir)
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
        )
        chunks = splitter.split_documents(documents)
        for index, chunk in enumerate(chunks, start=1):
            source = chunk.metadata.get("source", "unknown")
            page_part = f"-p{chunk.metadata['page_number']}" if "page_number" in chunk.metadata else ""
            stem = Path(source).stem.replace(" ", "_").lower()
            chunk.metadata["chunk_id"] = f"{stem}{page_part}-chunk-{index}"

        self.vector_store_manager.rebuild(chunks)
        return {
            "status": "completed",
            "documents_loaded": len(documents),
            "chunks_created": len(chunks),
            "collection_name": self.settings.collection_name,
            "persist_directory": str(self.vector_store_manager.persist_directory),
        }

    def _load_documents(self, doc_dir: Path) -> list[Document]:
        if not doc_dir.exists():
            raise FileNotFoundError(f"Document directory does not exist: {doc_dir}")

        documents: list[Document] = []
        for path in sorted(doc_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            if path.suffix.lower() in TEXT_EXTENSIONS:
                documents.append(self._load_text_document(path))
                continue

            if path.suffix.lower() in PDF_EXTENSIONS:
                documents.extend(self._load_pdf_documents(path))

        if not documents:
            raise ValueError(f"No supported documents were found in {doc_dir}")
        return documents

    @staticmethod
    def _load_text_document(path: Path) -> Document:
        content = path.read_text(encoding="utf-8")
        return Document(
            page_content=content,
            metadata={
                "source": str(path),
                "title": path.stem.replace("_", " ").title(),
                "file_type": path.suffix.lower().lstrip("."),
            },
        )

    @staticmethod
    def _load_pdf_documents(path: Path) -> list[Document]:
        reader = PdfReader(str(path))
        documents: list[Document] = []

        for page_index, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if not text:
                continue

            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": str(path),
                        "title": path.stem.replace("_", " ").title(),
                        "file_type": "pdf",
                        "page_number": page_index,
                    },
                )
            )

        if documents:
            return documents

        raise ValueError(
            f"PDF '{path}' did not yield extractable text. "
            "Use a text-based PDF or add OCR for scanned documents."
        )
