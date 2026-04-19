from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

from app.core.config import PROJECT_ROOT, get_settings
from app.mcp.contexts import RetrievedKnowledgeContext


class MCPClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        return asyncio.run(self._call_tool(name, arguments or {}))

    def list_tools(self) -> list[dict[str, Any]]:
        return asyncio.run(self._list_tools())

    def list_prompts(self) -> list[dict[str, Any]]:
        return asyncio.run(self._list_prompts())

    def list_resources(self) -> list[dict[str, Any]]:
        return asyncio.run(self._list_resources())

    def read_resource(self, uri: str) -> str:
        return asyncio.run(self._read_resource(uri))

    def get_prompt_messages(self, name: str, arguments: dict[str, str] | None = None) -> list[str]:
        return asyncio.run(self._get_prompt_messages(name, arguments or {}))

    def knowledge_lookup(self, query: str, top_k: int) -> RetrievedKnowledgeContext:
        result = self.call_tool("knowledge_lookup", {"query": query, "top_k": top_k})
        structured = result.get("structured") or {}
        return RetrievedKnowledgeContext.model_validate(structured)

    async def _call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        async with stdio_client(self._server_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(name, arguments=arguments)
                return {
                    "structured": getattr(result, "structuredContent", None),
                    "text": self._content_to_text(getattr(result, "content", [])),
                    "raw": result,
                }

    async def _list_tools(self) -> list[dict[str, Any]]:
        async with stdio_client(self._server_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                return [
                    {
                        "name": tool.name,
                        "description": tool.description or "",
                    }
                    for tool in result.tools
                ]

    async def _list_prompts(self) -> list[dict[str, Any]]:
        async with stdio_client(self._server_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_prompts()
                return [
                    {
                        "name": prompt.name,
                        "description": prompt.description or "",
                    }
                    for prompt in result.prompts
                ]

    async def _list_resources(self) -> list[dict[str, Any]]:
        async with stdio_client(self._server_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_resources()
                return [
                    {
                        "uri": str(resource.uri),
                        "name": resource.name or "",
                        "description": resource.description or "",
                    }
                    for resource in result.resources
                ]

    async def _read_resource(self, uri: str) -> str:
        async with stdio_client(self._server_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.read_resource(uri)
                return self._content_to_text(getattr(result, "contents", []))

    async def _get_prompt_messages(self, name: str, arguments: dict[str, str]) -> list[str]:
        async with stdio_client(self._server_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.get_prompt(name, arguments=arguments)
                return [self._content_to_text([message.content]) for message in result.messages]

    def _server_params(self) -> StdioServerParameters:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        return StdioServerParameters(
            command=sys.executable,
            args=["-m", self.settings.mcp_server_module],
            env=env,
            cwd=PROJECT_ROOT,
        )

    @staticmethod
    def _content_to_text(contents: list[Any]) -> str:
        parts: list[str] = []
        for content in contents:
            if isinstance(content, types.TextContent):
                parts.append(content.text)
                continue
            text = getattr(content, "text", None)
            if text:
                parts.append(str(text))
                continue
            parts.append(str(content))
        return "\n".join(part for part in parts if part).strip()
