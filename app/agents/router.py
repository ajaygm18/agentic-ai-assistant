from __future__ import annotations

import re

from app.mcp.contexts import MemoryContext, RouteType, RoutingDecision, UserQueryContext


class WorkflowRouter:
    _conversation_patterns = (
        "hello",
        "hi",
        "thanks",
        "thank you",
        "who are you",
        "how are you",
    )
    _knowledge_keywords = (
        "doc",
        "document",
        "handbook",
        "policy",
        "release",
        "architecture",
        "system",
        "internal",
        "knowledge base",
        "rag",
        "mcp",
    )
    _tool_keywords = (
        "calculate",
        "compute",
        "math",
        "timestamp",
        "date",
        "time",
        "today",
        "difference between",
        "sum",
        "multiply",
        "divide",
    )
    _complex_keywords = (
        "compare",
        "step by step",
        "also",
        "then",
        "and",
        "plan",
        "combine",
    )

    def route(self, user_query: UserQueryContext, memory: MemoryContext) -> RoutingDecision:
        text = user_query.normalized_query.lower()
        reasons: list[str] = []

        is_conversational = any(pattern in text for pattern in self._conversation_patterns) and len(text.split()) <= 12
        requests_knowledge = any(keyword in text for keyword in self._knowledge_keywords)
        requests_tools = any(keyword in text for keyword in self._tool_keywords) or bool(
            re.search(r"\d+\s*[\+\-\*/]\s*\d+", text)
        )
        requests_mcp_catalog = "mcp" in text and any(
            keyword in text
            for keyword in ("tool", "tools", "resource", "resources", "prompt", "prompts", "available", "list")
        )
        looks_complex = any(keyword in text for keyword in self._complex_keywords) and len(text.split()) > 8

        if requests_mcp_catalog:
            reasons.append("query asks for live MCP server capabilities")
            return RoutingDecision(route=RouteType.TOOL, rationale=reasons)

        if is_conversational and not requests_knowledge and not requests_tools:
            reasons.append("short conversational query without retrieval or tool signals")
            return RoutingDecision(route=RouteType.DIRECT, rationale=reasons)

        if requests_knowledge and requests_tools:
            reasons.append("query mixes internal knowledge lookup with calculation or time-sensitive operations")
            return RoutingDecision(route=RouteType.HYBRID, rationale=reasons)

        if requests_knowledge and looks_complex:
            reasons.append("query references internal knowledge and has multi-step phrasing")
            return RoutingDecision(route=RouteType.HYBRID, rationale=reasons)

        if requests_knowledge:
            reasons.append("query appears grounded in local documentation or internal context")
            return RoutingDecision(route=RouteType.RAG, rationale=reasons)

        if requests_tools:
            reasons.append("query requires precise deterministic computation or current timestamp data")
            return RoutingDecision(route=RouteType.TOOL, rationale=reasons)

        if looks_complex and memory.turns:
            reasons.append("query looks multi-step and has prior session context that may matter")
            return RoutingDecision(route=RouteType.HYBRID, rationale=reasons)

        reasons.append("defaulting to direct response with memory context")
        return RoutingDecision(route=RouteType.DIRECT, rationale=reasons)
