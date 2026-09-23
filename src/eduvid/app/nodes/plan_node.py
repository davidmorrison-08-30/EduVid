"""Plan node: extract intents, entities, and a scene plan from the concept."""
from __future__ import annotations

from ..llm import chat_json
from ..prompts import PLAN_SYSTEM_PROMPT
from ..schemas import Plan
from ..state import WorkflowState


def plan_node(state: WorkflowState) -> WorkflowState:
    concept = state["concept"]
    messages = [
        {"role": "system", "content": PLAN_SYSTEM_PROMPT},
        {"role": "user", "content": f"Chemistry concept: {concept}"},
    ]
    data = chat_json(messages)
    plan = Plan(
        intents=[str(x) for x in data.get("intents", [])],
        entities=[str(x) for x in data.get("entities", [])],
        scene_plan=[str(x) for x in data.get("scene_plan", [])],
    )
    return {
        "plan": plan,
        "codegen_iterations": 0,
        "alignment_iterations": 0,
        "aligned": False,
        "exec_error": False,
        "feedback": "",
    }
