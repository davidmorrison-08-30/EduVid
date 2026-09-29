"""Shared LangGraph state definition."""
from __future__ import annotations

from typing import Optional

from typing_extensions import TypedDict

from .schemas import Plan


class WorkflowState(TypedDict, total=False):
    """State threaded through the video-generation workflow.

    Attributes:
        job_id: Identifier used to name the output video.
        concept: The chemistry concept to explain (the user "utterance").
        plan: Extracted intents, entities, and scene plan.
        generation: The most recent generated Manim script as a Python string.
        feedback: Latest feedback (safety violation, alignment note, or exec error).
        safe: Whether the latest generated code passed static safety screening.
        aligned: Whether the code is judged aligned with the plan.
        exec_error: Whether the last render attempt failed.
        codegen_iterations: Number of code-generation attempts.
        alignment_iterations: Number of alignment evaluations performed.
        video_url: AWS S3 presigned URL of the video
        error: Terminal error message (set on failure).
    """

    job_id: str
    concept: str
    plan: Plan
    generation: str
    feedback: str
    safe: bool
    aligned: bool
    exec_error: bool
    codegen_iterations: int
    alignment_iterations: int
    video_url: Optional[str]
    error: Optional[str]
