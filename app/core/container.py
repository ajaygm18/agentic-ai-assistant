from __future__ import annotations

from functools import lru_cache

from app.agents.executor import AgentExecutor
from app.agents.planner import PlanBuilder
from app.agents.router import WorkflowRouter
from app.agents.service import AssistantService
from app.mcp.client import MCPClient
from app.memory.store import FileSessionStore
from app.rag.ingestion import DocumentIngestionService
from app.rag.retriever import KnowledgeRetriever
from app.rag.vectorstore import VectorStoreManager
from app.tools.registry import ToolRegistry


@lru_cache(maxsize=1)
def get_memory_store() -> FileSessionStore:
    return FileSessionStore()


@lru_cache(maxsize=1)
def get_vector_store_manager() -> VectorStoreManager:
    return VectorStoreManager()


@lru_cache(maxsize=1)
def get_retriever() -> KnowledgeRetriever:
    return KnowledgeRetriever(get_vector_store_manager())


@lru_cache(maxsize=1)
def get_mcp_client() -> MCPClient:
    return MCPClient()


@lru_cache(maxsize=1)
def get_tool_registry() -> ToolRegistry:
    return ToolRegistry(get_mcp_client())


@lru_cache(maxsize=1)
def get_assistant_service() -> AssistantService:
    return AssistantService(
        router=WorkflowRouter(),
        planner=PlanBuilder(get_mcp_client()),
        executor=AgentExecutor(get_tool_registry()),
        retriever=get_retriever(),
        memory_store=get_memory_store(),
        mcp_client=get_mcp_client(),
    )


@lru_cache(maxsize=1)
def get_ingestion_service() -> DocumentIngestionService:
    return DocumentIngestionService(get_vector_store_manager())
