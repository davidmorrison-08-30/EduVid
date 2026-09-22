"""Pydantic models for the API and the workflow."""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


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
    video_path: Optional[str] = None
    error: Optional[str] = None


class Plan(BaseModel):
    """Structured output of the plan node (intents + entities)."""

    intents: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    scene_plan: List[str] = Field(default_factory=list)


class AlignmentVerdict(BaseModel):
    """Result of the code-text alignment evaluation node."""

    aligned: bool = False
    feedback: str = ""
