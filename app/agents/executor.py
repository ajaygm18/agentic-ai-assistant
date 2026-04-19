from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from app.agents.prompts import build_system_prompt, build_user_prompt
from app.core.config import get_settings
from app.mcp.contexts import AgentExecutionState, ExecutionTraceItem, ToolResultContext
from app.services.llm import get_chat_model
from app.tools.registry import ToolRegistry


class AgentExecutor:
    def __init__(self, tool_registry: ToolRegistry) -> None:
        self.settings = get_settings()
        self.tool_registry = tool_registry

    def run(self, state: AgentExecutionState) -> str:
        if state.route.value == "direct":
            return self._run_direct(state)
        return self._run_with_tools(state)

    def _run_direct(self, state: AgentExecutionState) -> str:
        llm = get_chat_model(temperature=self.settings.llm_temperature)
        response = llm.invoke(self._build_messages(state))
        state.trace.append(
            ExecutionTraceItem(stage="generation", message="Generated direct response without tool calls.")
        )
        return self._coerce_content(response.content)

    def _run_with_tools(self, state: AgentExecutionState) -> str:
        if self._requires_manual_tool_path():
            return self._run_manual_tool_path(state)

        tools = self.tool_registry.get_tools(state.session_id)
        tool_map = {tool.name: tool for tool in tools}
        llm = get_chat_model(temperature=self.settings.llm_temperature).bind_tools(tools)
        messages = self._build_messages(state)

        for _ in range(self.settings.tool_loop_limit):
            ai_message = llm.invoke(messages)
            messages.append(ai_message)
            tool_calls = getattr(ai_message, "tool_calls", []) or []
            if not tool_calls:
                state.trace.append(
                    ExecutionTraceItem(stage="generation", message="Generated final response after tool-enabled loop.")
                )
                return self._coerce_content(ai_message.content)

            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_input = tool_call.get("args", {})
                tool = tool_map.get(tool_name)

                try:
                    if tool is None:
                        raise ValueError(f"Tool '{tool_name}' is not registered.")
                    raw_output = tool.invoke(tool_input)
                    output = self._stringify(raw_output)
                    status = "completed"
                except Exception as exc:  # noqa: BLE001
                    output = f"Tool execution failed: {exc}"
                    status = "failed"

                state.tool_results.append(
                    ToolResultContext(
                        tool_name=tool_name,
                        tool_input=tool_input,
                        status=status,
                        output=output,
                    )
                )
                state.trace.append(
                    ExecutionTraceItem(
                        stage="tool_call",
                        message=f"Executed tool '{tool_name}' with status '{status}'.",
                        data={"tool_name": tool_name, "status": status},
                    )
                )
                messages.append(ToolMessage(content=output, tool_call_id=tool_call["id"]))

        fallback = get_chat_model(temperature=self.settings.llm_temperature).invoke(messages)
        state.trace.append(
            ExecutionTraceItem(
                stage="generation",
                message="Reached tool loop limit and forced a final synthesis response.",
            )
        )
        return self._coerce_content(fallback.content)

    def _run_manual_tool_path(self, state: AgentExecutionState) -> str:
        tools = {tool.name: tool for tool in self.tool_registry.get_tools(state.session_id)}
        planned_calls = self._plan_manual_tool_calls(state)

        for tool_name, tool_input in planned_calls:
            tool = tools.get(tool_name)
            if tool is None:
                continue
            try:
                output = self._stringify(tool.invoke(tool_input))
                status = "completed"
            except Exception as exc:  # noqa: BLE001
                output = f"Tool execution failed: {exc}"
                status = "failed"

            state.tool_results.append(
                ToolResultContext(
                    tool_name=tool_name,
                    tool_input=tool_input,
                    status=status,
                    output=output,
                )
            )
            state.trace.append(
                ExecutionTraceItem(
                    stage="tool_call",
                    message=f"Executed manual tool '{tool_name}' with status '{status}'.",
                    data={"tool_name": tool_name, "status": status},
                )
            )

        llm = get_chat_model(temperature=self.settings.llm_temperature)
        response = llm.invoke(self._build_messages(state))
        state.trace.append(
            ExecutionTraceItem(
                stage="generation",
                message="Generated final response after manual tool execution.",
            )
        )
        return self._coerce_content(response.content)

    def _plan_manual_tool_calls(self, state: AgentExecutionState) -> list[tuple[str, dict[str, Any]]]:
        query = state.user_query.user_message.lower()
        calls: list[tuple[str, dict[str, Any]]] = []

        expression = self._extract_expression(state.user_query.user_message)
        if expression:
            calls.append(("calculator", {"expression": expression}))

        if any(keyword in query for keyword in ("time", "timestamp", "today", "date", "utc")):
            timezone_name = "UTC" if "utc" in query else None
            calls.append(("current_timestamp", {"timezone_name": timezone_name}))

        if "session" in query or "chat so far" in query or "conversation" in query:
            calls.append(("session_summary", {"max_turns": 6}))

        if state.route.value == "tool" and any(keyword in query for keyword in ("handbook", "policy", "release", "doc", "knowledge")):
            calls.append(("knowledge_lookup", {"query": state.user_query.user_message, "top_k": 3}))

        seen = set()
        unique_calls: list[tuple[str, dict[str, Any]]] = []
        for tool_name, tool_input in calls:
            key = (tool_name, json.dumps(tool_input, sort_keys=True))
            if key in seen:
                continue
            seen.add(key)
            unique_calls.append((tool_name, tool_input))
        return unique_calls

    @staticmethod
    def _extract_expression(text: str) -> str | None:
        matches = re.findall(r"[\d\.\+\-\*\/\(\)\s]+", text)
        candidates = [
            match.strip()
            for match in matches
            if match.strip() and re.search(r"\d", match) and re.search(r"[\+\-\*\/]", match)
        ]
        if not candidates:
            return None
        return max(candidates, key=len)

    def _requires_manual_tool_path(self) -> bool:
        return self.settings.llm_model.strip().lower() == "gpt-5.4"

    def _build_messages(self, state: AgentExecutionState) -> list[Any]:
        messages: list[Any] = [SystemMessage(content=build_system_prompt(state.route))]
        for turn in state.memory.turns:
            if turn.role == "user":
                messages.append(HumanMessage(content=turn.content))
            else:
                messages.append(AIMessage(content=turn.content))
        messages.append(HumanMessage(content=build_user_prompt(state)))
        return messages

    @staticmethod
    def _coerce_content(content: Any) -> str:
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            return "\n".join(
                str(part.get("text", part)) if isinstance(part, dict) else str(part)
                for part in content
            ).strip()
        return str(content).strip()

    @staticmethod
    def _stringify(value: Any) -> str:
        if isinstance(value, str):
            return value
        return json.dumps(value, default=str)
