"""Code execution node: render the generated Manim script to an MP4.

The script is written into an isolated temporary directory and rendered in a
subprocess with ``shell=False``, a list of arguments, a wall-clock timeout, a
reduced environment, and an isolated working directory. The resulting MP4 is
copied into the project ``outputs/`` directory. Any failure is reported back so
the workflow can route to the code-generation node for correction.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import uuid

import boto3
from botocore.exceptions import ClientError

from ..config import OUTPUT_DIR, RENDER_TIMEOUT_SECONDS
from ..prompts import SCENE_CLASS_NAME
from ..state import WorkflowState

# Environment variables that are safe/necessary to forward to the renderer.
_ENV_PASSTHROUGH = ("PATH", "LANG", "LC_ALL", "LC_CTYPE")

S3_BUCKET: str = "eduvid-storage" 
S3_PREFIX = "videos"
PRESIGNED_URL_EXPIRATION = 7 * 24 * 60 * 60 


def _build_env(sandbox: Path) -> dict[str, str]:
    import os

    env = {k: os.environ[k] for k in _ENV_PASSTHROUGH if k in os.environ}
    # Isolate any home/config/temp writes inside the sandbox.
    env["HOME"] = str(sandbox)
    env["TMPDIR"] = str(sandbox)
    env["PYTHONUNBUFFERED"] = "1"
    return env


def _truncate(text: str, limit: int = 2000) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[-limit:]


def _upload_to_s3(local_path: Path) -> tuple[str, str]:
    """Upload video to S3 and return (s3_key, presigned_url).
    
    Args:
        local_path: Path to the local MP4 file.
        job_id: Job identifier for the S3 key.
    
    Returns:
        Tuple of (s3_key, presigned_url).
    
    Raises:
        ClientError if the upload fails.
    """
    s3_key = f"{S3_PREFIX}/{uuid.uuid5()}.mp4"
    
    try:
        s3_client = boto3.client("s3")
        
        # Upload the file
        s3_client.upload_file(
            Filename=str(local_path),
            Bucket=S3_BUCKET,
            Key=s3_key,
            ExtraArgs={
                "ContentType": "video/mp4",
                "Metadata": {
                    "description": "Chemistry concept videos",
                }
            }
        )
        
        # Generate a presigned URL
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": "eduvid-storage", "Key": s3_key},
            ExpiresIn=PRESIGNED_URL_EXPIRATION,
        )
        
        return s3_key, presigned_url
    
    except ClientError as exc:
        raise RuntimeError(
            f"Failed to upload video to S3: {exc}"
        ) from exc


def execute_node(state: WorkflowState) -> WorkflowState:
    code: str = state["generation"]
    job_id = state["job_id"]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="manim_job_") as tmp:
        sandbox = Path(tmp)
        script_path = sandbox / "scene.py"
        script_path.write_text(code)
        media_dir = sandbox / "media"

        cmd = [
            sys.executable,
            "-m",
            "manim",
            "render",
            "-ql",
            "--format",
            "mp4",
            "--media_dir",
            str(media_dir),
            "--disable_caching",
            str(script_path),
            SCENE_CLASS_NAME,
        ]

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(sandbox),
                env=_build_env(sandbox),
                capture_output=True,
                text=True,
                timeout=RENDER_TIMEOUT_SECONDS,
                shell=False,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return {
                "exec_error": True,
                "feedback": (
                    f"Rendering timed out after {RENDER_TIMEOUT_SECONDS}s. Simplify the "
                    "animation (fewer/shorter plays) so it renders quickly."
                ),
            }

        if proc.returncode != 0:
            return {
                "exec_error": True,
                "feedback": (
                    "Rendering failed. Fix the Manim code based on this error:\n"
                    f"{_truncate(proc.stderr or proc.stdout)}"
                ),
            }

        produced = sorted(media_dir.rglob("*.mp4"))
        if not produced:
            return {
                "exec_error": True,
                "feedback": "Rendering finished but produced no MP4 file. Ensure the "
                f"Scene `{SCENE_CLASS_NAME}` plays at least one animation.",
            }

        final_path = OUTPUT_DIR / f"{job_id}.mp4"
        shutil.copy2(produced[0], final_path)

    try:
        s3_key, presigned_url = _upload_to_s3(local_final_path)
    except RuntimeError as exc:
        return {
            "exec_error": True,
            "feedback": str(exc),
        }

    return {
        "exec_error": False,
        "video_path": str(local_final_path),
        "s3_key": s3_key,
        "video_url": presigned_url,  # Presigned URL for download
        "feedback": "",
    }
