"""Code generation and correction node.

Adapted from the LangGraph coding-agent pattern (generate -> check -> refine):
it produces a single self-contained Manim script as a raw Python string and
statically screens it for dangerous commands before it is allowed downstream.
Any prior feedback (safety violation, misalignment, or render error) is fed back
into the prompt so the model can correct itself.
"""
from __future__ import annotations

import re

from ..prompts import CODEGEN_SYSTEM_PROMPT, SCENE_CLASS_NAME
from ..llm import chat
from ..safety import screen_code
from ..schemas import Plan
from ..state import WorkflowState

_CODE_FENCE = re.compile(r"```(?:python)?\s*(.*?)```", re.DOTALL)


def _strip_code_fence(text: str) -> str:
    """Return bare Python source, removing an optional markdown code fence."""
    match = _CODE_FENCE.search(text)
    if match:
        return match.group(1).strip()
    return text.strip()


def _build_user_message(state: WorkflowState) -> str:
    plan: Plan = state["plan"]
    parts = [
        f"Chemistry concept: {state['concept']}",
        f"Intents: {plan.intents}",
        f"Entities: {plan.entities}",
        f"Scene plan: {plan.scene_plan}",
        f"The Scene subclass MUST be named `{SCENE_CLASS_NAME}`.",
    ]
    feedback = state.get("feedback", "")
    if feedback:
        parts.append(
            "Your previous attempt must be corrected. Address this feedback precisely:\n"
            f"{feedback}"
        )
    return "\n".join(parts)


def codegen_node(state: WorkflowState) -> WorkflowState:
    messages = [
        {"role": "system", "content": CODEGEN_SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_message(state)},
    ]
    code = _strip_code_fence(chat(messages, max_tokens=6000))

    iterations = state.get("codegen_iterations", 0) + 1

    result = screen_code(code)
    if not result.safe:
        return {
            "generation": code,
            "safe": False,
            "feedback": (
                "The generated code failed the safety screen. Remove these and "
                f"regenerate using only allowed Manim/numpy/math APIs: {result.report}"
            ),
            "codegen_iterations": iterations,
        }

    if SCENE_CLASS_NAME not in code:
        return {
            "generation": code,
            "safe": False,
            "feedback": f"The script must define a Scene subclass named `{SCENE_CLASS_NAME}`.",
            "codegen_iterations": iterations,
        }

    return {
        "generation": code,
        "safe": True,
        "feedback": "",
        "codegen_iterations": iterations,
    }
