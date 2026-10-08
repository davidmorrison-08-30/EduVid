"""In-memory async job store and workflow runner."""
from __future__ import annotations

import threading
import uuid
from typing import Dict

from .graph import workflow
from .schemas import JobState, JobStatus
from .config import get_appsync_config

_jobs: Dict[str, JobStatus] = {}
_lock = threading.Lock()
appsync_cfg = get_appsync_config("eduvid-appsync")


def create_job(concept: str) -> JobStatus:
    job_id = uuid.uuid4().hex
    status = JobStatus(job_id=job_id, state=JobState.QUEUED, concept=concept)
    with _lock:
        _jobs[job_id] = status
    return status


def get_job(job_id: str) -> JobStatus | None:
    with _lock:
        return _jobs.get(job_id)


def _set(job_id: str, **fields) -> None:
    with _lock:
        current = _jobs.get(job_id)
        if current is not None:
            _jobs[job_id] = current.model_copy(update=fields)


def notify_job_completion(job_id: str, 
                          status: str,
                          video_url: str=""):
    query = """
    mutation PublishJobStatus($jobId: ID!, $status: String!, $videoUrl: String) {
      publishJobStatus(jobId: $jobId, status: $status, videoUrl: $videoUrl) {
        jobId
        status
        videoUrl
      }
    }
    """
    variables = {
        "jobId": job_id,
        "status": status,
        "videoUrl": video_url
    }
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": cfg["APPSYNC_API_KEY"]
    }
    
    response = requests.post(
        cfg["APPSYNC_GRAPHQL"], 
        json={"query": query, "variables": variables}, 
        headers=headers
    )


def run_job(job_id: str) -> None:
    """Execute the workflow for a job (intended to run in the background)."""
    job = get_job(job_id)
    if job is None:
        return

    _set(job_id, state=JobState.RUNNING)
    initial_state = {
        "job_id": job_id,
        "concept": job.concept,
        "codegen_iterations": 0,
        "alignment_iterations": 0,
    }
    try:
        final_state = workflow.invoke(initial_state)
    except Exception as exc:  # noqa: BLE001 - surface any failure to the caller
        _set(job_id, state=JobState.FAILED, error=str(exc))
        return

    video_url = final_state.get("video_url")
    if video_url:
        _set(job_id, state=JobState.SUCCEEDED, video_url=video_url)
        notify_job_completion(job_id, status=JobState.SUCCEEDED, video_url=video_url)
    else:
        _set(
            job_id,
            state=JobState.FAILED,
            error=final_state.get("error", "Unknown workflow failure."),
        )
        notify_job_completion(job_id, status=JobState.FAILED)
