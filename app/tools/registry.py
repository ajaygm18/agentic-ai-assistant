from __future__ import annotations

from app.mcp.client import MCPClient
from app.tools.implementations import (
    CalculatorInput,
    KnowledgeLookupInput,
    SessionSummaryInput,
    TimestampInput,
)
from langchain_core.tools import BaseTool, StructuredTool


class ToolRegistry:
    def __init__(self, mcp_client: MCPClient) -> None:
        self.mcp_client = mcp_client

    def get_tools(self, session_id: str) -> list[BaseTool]:
        def calculator(expression: str) -> str:
            return self.mcp_client.call_tool("calculator", {"expression": expression})["text"]

        def current_timestamp(timezone_name: str | None = None) -> str:
            return self.mcp_client.call_tool("current_timestamp", {"timezone_name": timezone_name})["text"]

        def knowledge_lookup(query: str, top_k: int = 3) -> str:
            result = self.mcp_client.call_tool("knowledge_lookup", {"query": query, "top_k": top_k})
            return result["text"] or str(result["structured"])

        def session_summary(max_turns: int = 6) -> str:
            return self.mcp_client.call_tool(
                "session_summary",
                {"session_id": session_id, "max_turns": max_turns},
            )["text"]

        return [
            StructuredTool.from_function(
                func=calculator,
                name="calculator",
                description="Evaluate arithmetic expressions exactly.",
                args_schema=CalculatorInput,
            ),
            StructuredTool.from_function(
                func=current_timestamp,
                name="current_timestamp",
                description="Return the current date and timestamp, optionally for a named timezone.",
                args_schema=TimestampInput,
            ),
            StructuredTool.from_function(
                func=knowledge_lookup,
                name="knowledge_lookup",
                description="Search the local RAG knowledge base for internal documentation.",
                args_schema=KnowledgeLookupInput,
            ),
            StructuredTool.from_function(
                func=session_summary,
                name="session_summary",
                description="Summarize recent turns from the current conversation session.",
                args_schema=SessionSummaryInput,
            ),
        ]
