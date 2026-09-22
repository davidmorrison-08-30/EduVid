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

from ..config import OUTPUT_DIR, RENDER_TIMEOUT_SECONDS
from ..prompts import SCENE_CLASS_NAME
from ..state import WorkflowState

# Environment variables that are safe/necessary to forward to the renderer.
_ENV_PASSTHROUGH = ("PATH", "LANG", "LC_ALL", "LC_CTYPE")


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

    return {
        "exec_error": False,
        "video_path": str(final_path),
        "feedback": "",
    }
