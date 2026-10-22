"""Assemble the LangGraph video-generation workflow.

Flow:

  START -> answer -> code agent -> END
          ^     |        ^    |      
          |--error       |--error

"""

from __future__ import annotations
from langgraph.graph import END, START, StateGraph
from .utils.config import MAX_ANSWER_RETRIES, MAX_AGENT_RETRIES
from .nodes.answer_node import answer_node
from .nodes.coding_agent import agent_node 
from .schemas import WorkflowState


def route_after_answer(state: WorkflowState) -> str:
    """Successful answer returned by LLM proceeds to next node; failed one gets regenerated"""
    if not state.get("answer_error", False):
        return "agent"
    if state.get("answer_iterations", 0) < MAX_ANSWER_RETRIES:
        return "answer"
    return "fail"


def route_after_agent(state: WorkflowState) -> str:
    """Successful render ends; render errors regenerate until capped."""
    if not state.get("agent_error", False):
        return "succeed"
    if state.get("agent_iterations", 0) < MAX_AGENT_RETRIES:
        return "agent"
    return "fail"


def fail_node(state: WorkflowState) -> WorkflowState:
    error = ""
    if state.get("answer_error", False):
        error = error + f"Error in answering the user's question: {state["answer_error"]}\n"
    if state.get("agent_error", False):
        error = error + f"Error in video generation: {state["codegen_error"]}\n"
    return {
        "error": error,
        "video_url": None,
    }


def build_workflow():
    builder = StateGraph(WorkflowState)

    builder.add_node("answer", answer_node)
    builder.add_node("agent", agent_node)
    builder.add_node("fail", fail_node)

    builder.add_edge(START, "answer")
    builder.add_conditional_edges(
        "answer",
        route_after_answer,
        {"answer": "answer", "agent": "agent", "fail": "fail"},
    )
    builder.add_conditional_edges(
        "agent",
        route_after_agent,
        {"succeed": END, "agent": "agent", "fail": "fail"},
    )
    builder.add_edge("fail", END)

    return builder.compile()


workflow = build_workflow()
