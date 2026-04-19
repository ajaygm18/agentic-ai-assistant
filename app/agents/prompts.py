from __future__ import annotations

from app.mcp.contexts import AgentExecutionState, RouteType
from app.rag.retriever import KnowledgeRetriever


def build_system_prompt(route: RouteType) -> str:
    base = (
        "You are a production-grade agentic assistant exposed through an API. "
        "Answer clearly, stay grounded in retrieved context when it exists, and cite sources "
        "using square-bracket source ids such as [release_notes_chunk_1]. "
        "Use tools only when they materially improve accuracy. "
        "If the question depends on internal knowledge but no relevant passages are available, say that the knowledge base is missing or insufficient."
    )

    if route == RouteType.DIRECT:
        return base + " This request was routed as conversational/direct, so answer directly with memory awareness."
    if route == RouteType.RAG:
        return base + " This request was routed to retrieval-first mode. Prefer retrieved knowledge over unsupported assumptions."
    if route == RouteType.TOOL:
        return base + " This request was routed to tool-first mode. Use tools whenever they add precision."
    return base + " This request was routed to hybrid mode. Combine retrieval, tools, and synthesis when helpful."


def build_user_prompt(state: AgentExecutionState) -> str:
    plan_lines = "\n".join(
        f"- {step.title}: {step.description}" for step in state.plan
    ) or "- Answer directly."

    memory_lines = "\n".join(
        f"- {turn.role}: {turn.content}" for turn in state.memory.turns
    ) or "- No prior session memory."

    retrieved_context = KnowledgeRetriever.format_for_prompt(state.retrieved_knowledge)
    tool_lines = "\n".join(
        f"- {result.tool_name}({result.tool_input}): {result.output}"
        for result in state.tool_results
    ) or "- No tool results yet."

    return (
        f"Execution route: {state.route.value}\n"
        f"Routing rationale: {'; '.join(state.routing.rationale) or 'No rationale recorded.'}\n\n"
        f"Execution plan:\n{plan_lines}\n\n"
        f"Conversation memory:\n{memory_lines}\n\n"
        f"Retrieved knowledge:\n{retrieved_context}\n\n"
        f"Tool results:\n{tool_lines}\n\n"
        f"User request:\n{state.user_query.user_message}\n\n"
        "Return a final answer that is safe to expose through the API response. "
        "Do not reveal hidden chain-of-thought. Provide only the user-facing answer."
    )
