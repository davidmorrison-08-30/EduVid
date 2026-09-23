"""Assemble the LangGraph video-generation workflow.

Flow (see wf_planning.txt):

    START -> plan -> codegen -> alignment -> execute -> END
                       ^   |        |           |
                       |   |(unsafe)|(misaligned)|(render error)
                       +---+--------+-----------+

All back-edges return to ``codegen`` and are bounded by iteration caps so the
graph always terminates.
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .config import MAX_ALIGNMENT_RETRIES, MAX_CODEGEN_RETRIES
from .nodes.alignment_node import alignment_node
from .nodes.codegen_node import codegen_node
from .nodes.execute_node import execute_node
from .nodes.plan_node import plan_node
from .state import WorkflowState

from bedrock_agentcore.runtime import BedrockAgentCoreApp


def _route_after_codegen(state: WorkflowState) -> str:
    """Safe code proceeds to alignment; unsafe code regenerates until capped."""
    if state.get("safe", False):
        return "alignment"
    if state.get("codegen_iterations", 0) < MAX_CODEGEN_RETRIES:
        return "codegen"
    return "fail"


def _route_after_alignment(state: WorkflowState) -> str:
    """Aligned code is executed; misaligned code regenerates until capped."""
    if state.get("aligned", False):
        return "execute"
    if (
        state.get("alignment_iterations", 0) < MAX_ALIGNMENT_RETRIES
        and state.get("codegen_iterations", 0) < MAX_CODEGEN_RETRIES
    ):
        return "codegen"
    # Out of retries: proceed with the best available code.
    return "execute"


def _route_after_execute(state: WorkflowState) -> str:
    """Successful render ends; render errors regenerate until capped."""
    if not state.get("exec_error", False):
        return "succeed"
    if state.get("codegen_iterations", 0) < MAX_CODEGEN_RETRIES:
        return "codegen"
    return "fail"


def _fail_node(state: WorkflowState) -> WorkflowState:
    return {
        "error": state.get("feedback")
        or "Failed to generate a valid video after maximum retries.",
        "video_path": None,
    }


def build_workflow():
    builder = StateGraph(WorkflowState)

    builder.add_node("planner", plan_node)
    builder.add_node("codegen", codegen_node)
    builder.add_node("alignment", alignment_node)
    builder.add_node("execute", execute_node)
    builder.add_node("fail", _fail_node)

    builder.add_edge(START, "planner")
    builder.add_edge("planner", "codegen")
    builder.add_conditional_edges(
        "codegen",
        _route_after_codegen,
        {"alignment": "alignment", "codegen": "codegen", "fail": "fail"},
    )
    builder.add_conditional_edges(
        "alignment",
        _route_after_alignment,
        {"execute": "execute", "codegen": "codegen"},
    )
    builder.add_conditional_edges(
        "execute",
        _route_after_execute,
        {"succeed": END, "codegen": "codegen", "fail": "fail"},
    )
    builder.add_edge("fail", END)

    return builder.compile()


# Compiled once and reused across requests.
workflow = build_workflow()
