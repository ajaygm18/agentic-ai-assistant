from __future__ import annotations

from app.agents.executor import AgentExecutor
from app.agents.planner import PlanBuilder
from app.agents.router import WorkflowRouter
from app.core.config import get_settings
from app.mcp.client import MCPClient
from app.mcp.contexts import AgentExecutionState, ConversationTurn, ExecutionTraceItem, UserQueryContext
from app.models.api import ChatResponse
from app.memory.base import BaseMemoryStore
from app.rag.retriever import KnowledgeRetriever


class AssistantService:
    def __init__(
        self,
        router: WorkflowRouter,
        planner: PlanBuilder,
        executor: AgentExecutor,
        retriever: KnowledgeRetriever,
        memory_store: BaseMemoryStore,
        mcp_client: MCPClient,
    ) -> None:
        self.settings = get_settings()
        self.router = router
        self.planner = planner
        self.executor = executor
        self.retriever = retriever
        self.memory_store = memory_store
        self.mcp_client = mcp_client

    def chat(self, session_id: str, user_message: str) -> ChatResponse:
        clean_message = user_message.strip()
        user_query = UserQueryContext(
            session_id=session_id,
            user_message=clean_message,
            normalized_query=clean_message,
        )
        memory_context = self.memory_store.build_context(session_id, self.settings.memory_window)
        routing = self.router.route(user_query, memory_context)
        plan = self.planner.build(routing, user_query, memory_context)

        state = AgentExecutionState(
            session_id=session_id,
            route=routing.route,
            user_query=user_query,
            memory=memory_context,
            routing=routing,
            plan=plan,
        )
        state.trace.append(
            ExecutionTraceItem(
                stage="routing",
                message=f"Selected '{routing.route.value}' workflow.",
                data={"rationale": routing.rationale},
            )
        )

        if routing.route.value in {"rag", "hybrid"}:
            state.retrieved_knowledge = self.mcp_client.knowledge_lookup(
                user_query.user_message,
                top_k=self.settings.retriever_top_k,
            )
            state.trace.append(
                ExecutionTraceItem(
                    stage="retrieval",
                    message="Retrieved knowledge context from vector store.",
                    data={"total_hits": state.retrieved_knowledge.total_hits},
                )
            )

        final_answer = self.executor.run(state)
        state.final_answer = final_answer

        self.memory_store.append_turn(
            session_id,
            ConversationTurn(role="user", content=clean_message),
        )
        updated_session = self.memory_store.append_turn(
            session_id,
            ConversationTurn(role="assistant", content=final_answer),
        )
        state.trace.append(
            ExecutionTraceItem(
                stage="memory",
                message="Persisted user and assistant turns to session memory.",
                data={"turn_count": len(updated_session.turns)},
            )
        )

        sources = state.retrieved_knowledge.citations if state.retrieved_knowledge else []
        tools_used = list(dict.fromkeys(result.tool_name for result in state.tool_results))

        return ChatResponse(
            session_id=session_id,
            route=state.route,
            answer=final_answer,
            sources=sources,
            tools_used=tools_used,
            execution_summary=state.trace,
            memory_turn_count=len(updated_session.turns),
            session_updated_at=updated_session.updated_at,
        )
