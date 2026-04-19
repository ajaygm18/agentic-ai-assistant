from __future__ import annotations

from app.mcp.client import MCPClient
from app.tools.implementations import (
    CalculatorInput,
    KnowledgeLookupInput,
    McpCatalogInput,
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

        def mcp_catalog(include_prompts: bool = True, include_resources: bool = True) -> str:
            tools = self.mcp_client.list_tools()
            lines = ["Available MCP tools:"]
            for tool in tools:
                description = f" - {tool['description']}" if tool.get("description") else ""
                lines.append(f"- {tool['name']}{description}")

            if include_prompts:
                prompts = self.mcp_client.list_prompts()
                lines.append("\nAvailable MCP prompts:")
                for prompt in prompts:
                    description = f" - {prompt['description']}" if prompt.get("description") else ""
                    lines.append(f"- {prompt['name']}{description}")

            if include_resources:
                resources = self.mcp_client.list_resources()
                lines.append("\nAvailable MCP resources:")
                for resource in resources:
                    label = resource.get("uri") or resource.get("name")
                    description = f" - {resource['description']}" if resource.get("description") else ""
                    lines.append(f"- {label}{description}")

            return "\n".join(lines)

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
            StructuredTool.from_function(
                func=mcp_catalog,
                name="mcp_catalog",
                description="List live MCP tools, prompts, and resources exposed by the assistant MCP server.",
                args_schema=McpCatalogInput,
            ),
        ]
