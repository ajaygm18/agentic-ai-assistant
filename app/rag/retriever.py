from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings
from app.mcp.contexts import RetrievedKnowledgeContext, SourceCitation, UserQueryContext
from app.rag.vectorstore import VectorStoreManager


class KnowledgeRetriever:
    def __init__(self, vector_store_manager: VectorStoreManager) -> None:
        self.settings = get_settings()
        self.vector_store_manager = vector_store_manager

    def retrieve(
        self,
        user_query: UserQueryContext,
        top_k: int | None = None,
    ) -> RetrievedKnowledgeContext:
        store = self.vector_store_manager.load()
        if store is None:
            return RetrievedKnowledgeContext(query=user_query.user_message, available=False, total_hits=0)

        results = store.similarity_search_with_score(
            user_query.normalized_query,
            k=top_k or self.settings.retriever_top_k,
        )

        citations: list[SourceCitation] = []
        for rank, (document, distance) in enumerate(results, start=1):
            metadata = document.metadata or {}
            source_path = str(metadata.get("source", "unknown"))
            citations.append(
                SourceCitation(
                    source_id=str(metadata.get("chunk_id", f"chunk-{rank}")),
                    title=str(metadata.get("title", Path(source_path).stem)),
                    source_path=source_path,
                    relevance_score=round(1 / (1 + float(distance)), 4),
                    excerpt=document.page_content[:320].strip(),
                )
            )

        return RetrievedKnowledgeContext(
            query=user_query.user_message,
            available=bool(citations),
            total_hits=len(citations),
            citations=citations,
        )

    @staticmethod
    def format_for_prompt(context: RetrievedKnowledgeContext | None) -> str:
        if context is None or not context.citations:
            return "No retrieved knowledge was available."

        lines = []
        for citation in context.citations:
            lines.append(
                f"[{citation.source_id}] {citation.title} | {citation.source_path} | "
                f"score={citation.relevance_score}\n{citation.excerpt}"
            )
        return "\n\n".join(lines)
