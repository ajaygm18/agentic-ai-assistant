from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from app.core.config import get_settings
from app.memory.store import FileSessionStore
from app.mcp.contexts import RetrievedKnowledgeContext, UserQueryContext
from app.rag.retriever import KnowledgeRetriever
from app.rag.vectorstore import VectorStoreManager
from app.tools.implementations import (
    build_session_summary,
    get_current_timestamp,
    safe_calculate,
)


settings = get_settings()
memory_store = FileSessionStore()
vector_store_manager = VectorStoreManager()
retriever = KnowledgeRetriever(vector_store_manager)

mcp = FastMCP(
    "Agentic Assistant MCP Server",
    instructions=(
        "Provides shared tools, resources, and prompts for the Agentic AI Assistant. "
        "Use tools for deterministic actions, resources for contextual state, and prompts for reusable templates."
    ),
    json_response=True,
    streamable_http_path="/",
)


@mcp.tool()
def calculator(expression: str) -> str:
    """Evaluate arithmetic expressions exactly."""
    return str(safe_calculate(expression))


@mcp.tool()
def current_timestamp(timezone_name: str | None = None) -> str:
    """Return the current date and timestamp, optionally for a named timezone."""
    return get_current_timestamp(timezone_name)


@mcp.tool()
def session_summary(session_id: str, max_turns: int = 6) -> str:
    """Summarize recent turns from a conversation session."""
    session = memory_store.get_session(session_id)
    return build_session_summary(session, max_turns=max_turns)


@mcp.tool()
def knowledge_lookup(query: str, top_k: int = 3) -> dict[str, Any]:
    """Search the local vector store and return structured citations."""
    user_query = UserQueryContext(
        session_id="mcp-knowledge-lookup",
        user_message=query,
        normalized_query=query.strip(),
    )
    result = retriever.retrieve(user_query, top_k=top_k)
    return result.model_dump(mode="json")


@mcp.resource("session://{session_id}")
def session_resource(session_id: str) -> str:
    """Expose a session transcript as JSON."""
    return json.dumps(memory_store.get_session(session_id).model_dump(mode="json"), indent=2)


@mcp.resource("knowledge://catalog")
def knowledge_catalog() -> str:
    """Expose knowledge-base metadata for clients."""
    payload = {
        "docs_dir": str(settings.docs_dir),
        "collection_name": settings.collection_name,
        "persist_directory": str(settings.chroma_persist_directory),
        "indexed_chunks": vector_store_manager.count_chunks(),
    }
    return json.dumps(payload, indent=2)


@mcp.prompt()
def planning_prompt(route: str, rationale: str, user_message: str, memory_summary: str = "none") -> str:
    """Reusable planner prompt for building short execution plans."""
    return (
        "Create a concise execution plan for the assistant.\n"
        f"Route: {route}\n"
        f"Rationale: {rationale}\n"
        f"User message: {user_message}\n"
        f"Memory summary: {memory_summary}\n"
        'Return JSON with this shape: {"steps":[{"title":"string","description":"string","requires_retrieval":true,"allows_tools":false}]}.'
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
