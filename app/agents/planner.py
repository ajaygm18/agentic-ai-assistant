from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.mcp.client import MCPClient
from app.mcp.contexts import MemoryContext, PlanStep, RouteType, RoutingDecision, UserQueryContext
from app.services.llm import get_planner_model


class PlannedStep(BaseModel):
    title: str = Field(..., min_length=1, max_length=80)
    description: str = Field(..., min_length=1, max_length=220)
    requires_retrieval: bool = False
    allows_tools: bool = False


class PlannerOutput(BaseModel):
    steps: list[PlannedStep] = Field(default_factory=list, max_length=4)


class PlanBuilder:
    def __init__(self, mcp_client: MCPClient | None = None) -> None:
        self.mcp_client = mcp_client or MCPClient()

    def build(
        self,
        decision: RoutingDecision,
        user_query: UserQueryContext,
        memory: MemoryContext,
    ) -> list[PlanStep]:
        fallback = self._build_fallback(decision)
        try:
            planner = get_planner_model()
            prompt_messages = self.mcp_client.get_prompt_messages(
                "planning_prompt",
                {
                    "route": decision.route.value,
                    "rationale": "; ".join(decision.rationale) or "none",
                    "user_message": user_query.user_message,
                    "memory_summary": memory.summary or "none",
                },
            )
            response = planner.invoke(
                [
                    SystemMessage(
                        content=(
                            "You are the planning model for an API assistant. "
                            "Return valid JSON only using this schema exactly: "
                            '{"steps":[{"title":"string","description":"string","requires_retrieval":true,"allows_tools":false}]}. '
                            "Use 2 to 4 steps, keep them concise, and align them with the requested route."
                        )
                    ),
                    HumanMessage(content="\n\n".join(prompt_messages)),
                ]
            )
            parsed = PlannerOutput.model_validate(json.loads(self._coerce_content(response.content)))
            if parsed.steps:
                return [
                    PlanStep(
                        step_id=f"step-{index}",
                        title=step.title,
                        description=step.description,
                        requires_retrieval=step.requires_retrieval,
                        allows_tools=step.allows_tools,
                    )
                    for index, step in enumerate(parsed.steps, start=1)
                ]
        except Exception:  # noqa: BLE001
            pass
        return fallback

    def _build_fallback(self, decision: RoutingDecision) -> list[PlanStep]:
        if decision.route == RouteType.DIRECT:
            return [
                PlanStep(
                    step_id="memory",
                    title="Load conversation memory",
                    description="Hydrate recent turns for conversational continuity.",
                ),
                PlanStep(
                    step_id="respond",
                    title="Respond directly",
                    description="Generate an answer without retrieval or tool usage unless explicitly needed.",
                ),
            ]

        if decision.route == RouteType.RAG:
            return [
                PlanStep(
                    step_id="retrieve",
                    title="Retrieve knowledge",
                    description="Fetch the most relevant document chunks from the vector store.",
                    requires_retrieval=True,
                ),
                PlanStep(
                    step_id="synthesize",
                    title="Grounded synthesis",
                    description="Answer using retrieved evidence and cite sources.",
                ),
            ]

        if decision.route == RouteType.TOOL:
            return [
                PlanStep(
                    step_id="tooling",
                    title="Execute tools",
                    description="Use deterministic tools for calculations, timestamps, or other exact operations.",
                    allows_tools=True,
                ),
                PlanStep(
                    step_id="synthesize",
                    title="Compose answer",
                    description="Translate tool outputs into a concise final response.",
                ),
            ]

        return [
            PlanStep(
                step_id="retrieve",
                title="Retrieve knowledge",
                description="Gather relevant internal context from the vector store.",
                requires_retrieval=True,
            ),
            PlanStep(
                step_id="tooling",
                title="Execute tools",
                description="Use tools for exact operations or follow-up lookups when needed.",
                allows_tools=True,
            ),
            PlanStep(
                step_id="synthesize",
                title="Grounded synthesis",
                description="Merge retrieved evidence, tool outputs, and conversation memory into the final answer.",
            ),
        ]

    @staticmethod
    def _coerce_content(content: object) -> str:
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            return "\n".join(
                str(part.get("text", part)) if isinstance(part, dict) else str(part)
                for part in content
            ).strip()
        return str(content).strip()
