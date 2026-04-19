from __future__ import annotations

import ast
import operator
from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

from app.memory.base import SessionRecord
from app.mcp.contexts import RetrievedKnowledgeContext


class CalculatorInput(BaseModel):
    expression: str = Field(..., description="Arithmetic expression such as '(42 / 6) + 7'.")


class KnowledgeLookupInput(BaseModel):
    query: str = Field(..., description="Internal knowledge-base question.")
    top_k: int = Field(default=3, ge=1, le=8)


class TimestampInput(BaseModel):
    timezone_name: str | None = Field(
        default=None,
        description="Optional IANA timezone such as 'Asia/Kolkata' or 'UTC'.",
    )


class SessionSummaryInput(BaseModel):
    max_turns: int = Field(default=6, ge=1, le=12)


ALLOWED_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}

ALLOWED_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

ALLOWED_FUNCTIONS = {
    "abs": abs,
    "round": round,
}


def safe_calculate(expression: str) -> float:
    node = ast.parse(expression, mode="eval")
    return float(_evaluate_node(node.body))


def _evaluate_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)

    if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_BIN_OPS:
        left = _evaluate_node(node.left)
        right = _evaluate_node(node.right)
        return float(ALLOWED_BIN_OPS[type(node.op)](left, right))

    if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_UNARY_OPS:
        value = _evaluate_node(node.operand)
        return float(ALLOWED_UNARY_OPS[type(node.op)](value))

    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ALLOWED_FUNCTIONS:
        args = [_evaluate_node(arg) for arg in node.args]
        return float(ALLOWED_FUNCTIONS[node.func.id](*args))

    raise ValueError("Only arithmetic expressions using numbers, parentheses, abs, and round are supported.")


def get_current_timestamp(timezone_name: str | None = None) -> str:
    tz = ZoneInfo(timezone_name) if timezone_name else datetime.now().astimezone().tzinfo
    now = datetime.now(tz=tz)
    return now.isoformat()


def format_knowledge_lookup(context: RetrievedKnowledgeContext) -> str:
    if not context.available or not context.citations:
        return "No matching knowledge-base passages were found."

    lines = []
    for citation in context.citations:
        lines.append(
            f"[{citation.source_id}] {citation.title} ({citation.source_path})\n"
            f"score={citation.relevance_score}\n"
            f"{citation.excerpt}"
        )
    return "\n\n".join(lines)


def build_session_summary(session: SessionRecord, max_turns: int) -> str:
    recent_turns = session.turns[-max_turns:]
    if not recent_turns:
        return "This session does not have any prior turns."

    lines = [f"{turn.role}: {turn.content[:220]}" for turn in recent_turns]
    return "Recent session turns:\n" + "\n".join(lines)
