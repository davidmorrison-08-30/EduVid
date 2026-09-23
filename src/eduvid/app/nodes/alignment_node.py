"""Code-text alignment evaluation node (LLM-as-judge).

Checks whether the generated Manim script faithfully covers the plan's intents
and entities. If not aligned, the verdict feedback is routed back to the code
generation node.
"""
from __future__ import annotations

from ..llm import chat_json
from ..prompts import ALIGNMENT_SYSTEM_PROMPT
from ..schemas import AlignmentVerdict, Plan
from ..state import WorkflowState


def alignment_node(state: WorkflowState) -> WorkflowState:
    plan: Plan = state["plan"]
    code: str = state["generation"]
    user_content = (
        f"Concept: {state['concept']}\n"
        f"Intents: {plan.intents}\n"
        f"Entities: {plan.entities}\n"
        f"Scene plan: {plan.scene_plan}\n\n"
        f"Candidate Manim script:\n```python\n{code}\n```"
    )
    messages = [
        {"role": "system", "content": ALIGNMENT_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    data = chat_json(messages)
    verdict = AlignmentVerdict(
        aligned=bool(data.get("aligned", False)),
        feedback=str(data.get("feedback", "")),
    )

    iterations = state.get("alignment_iterations", 0) + 1
    update: WorkflowState = {
        "aligned": verdict.aligned,
        "alignment_iterations": iterations,
    }
    if not verdict.aligned:
        update["feedback"] = (
            "The code is not yet aligned with the plan. Improve it to address: "
            f"{verdict.feedback}"
        )
    return update
