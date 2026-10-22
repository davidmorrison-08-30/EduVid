"""Pydantic models for the API and the workflow."""
from __future__ import annotations
from enum import Enum
from typing import List, Optional, Annotated
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from .nodes.e2b_backend import ScopedE2BSandbox


class GenerateRequest(BaseModel):
    """Input payload for the video generation endpoint."""

    concept: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="The chemistry concept to explain in a short video.",
    )


class JobState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class GenerateResponse(BaseModel):
    job_id: str
    state: JobState


class JobStatus(BaseModel):
    job_id: str
    state: JobState
    concept: str
    video_url: Optional[str] = None
    error: Optional[str] = None


class WorkflowState(TypedDict, total=False):
    """State threaded through the video-generation workflow.

    Attributes:
        job_id: Identifier used to name the output video
        question: User's question
        answer: LLM-generated answer
        agent_iterations: Number of agent attempts
        answer_iterations: Number of answering attempts
        video_url: AWS S3 presigned URL of the video
        error: Accumulated error messages from agent and answer nodes
    """

    job_id: str
    question: str
    answer: str
    agent_iterations: int
    answer_iterations: int
    agent_error: Optional[str]
    answer_error: Optional[str]
    error: Optional[str]
    video_url: Optional[str]