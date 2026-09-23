"""Prompt templates and shared constants for the workflow nodes."""
from __future__ import annotations

from pathlib import Path

# The generated Manim script must define exactly this Scene subclass.
SCENE_CLASS_NAME = "ConceptScene"

_MANIM_NOTES_PATH = Path(__file__).resolve().parent.parent / "ref_docs" / "manim_notes.md"


def _load_manim_notes() -> str:
    """Load the persisted Manim reference notes to ground the codegen prompt."""
    try:
        return _MANIM_NOTES_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


MANIM_REFERENCE = _load_manim_notes()

PLAN_SYSTEM_PROMPT = """You are an instructional designer for short educational chemistry videos.
Given a chemistry concept, extract a structured plan using the chatbot notions of
intents and entities:
- intents: the learner-facing goals of the video (what understanding it should deliver).
- entities: the concrete chemistry data points to visualize (molecules, atoms, ions,
  bond types, reactions, quantities, states of matter, etc.).
- scene_plan: an ordered list of short visual beats describing what appears on
  screen over time (title, build-up, key idea, summary).

Respond with ONLY a JSON object of this exact shape:
{"intents": ["..."], "entities": ["..."], "scene_plan": ["beat 1", "beat 2", "..."]}
Keep it concise and strictly valid JSON. No prose outside the JSON."""

_CODEGEN_REQUIREMENTS = f"""You are an expert Manim (Community Edition) developer.
You write a single, self-contained Python script that renders a short, silent,
educational chemistry animation.

Hard requirements:
- Define exactly one Scene subclass named `{SCENE_CLASS_NAME}` with a `construct` method.
- `from manim import *` is allowed. You may also use `numpy`, `math`, `random`, `typing`.
- Do NOT import or use: os, sys, subprocess, shutil, socket, urllib, requests, pathlib,
  tempfile, importlib, pickle, ctypes, threading, asyncio, builtins.
- Do NOT call eval, exec, compile, open, __import__, input, getattr/setattr, or access
  dunder internals (__globals__, __subclasses__, __builtins__, etc.).
- Do NOT read or write any files or access the network. The only output is the rendered video.
- Use only Pango `Text(...)` for text. NEVER use `Tex`, `MathTex`, or anything LaTeX-based.
- Keep the total animation roughly 12-25 seconds; use self.play(...) and self.wait(...).
- Visualize chemistry with shapes (Circle for atoms/electrons, Line for bonds, VGroup for
  molecules), colors, and Text labels. Keep elements on-screen and non-overlapping.
- The code must run headless and be deterministic."""

_CODEGEN_REFERENCE = (
    (
        "Use the following Manim reference documentation as the authoritative guide "
        "for available APIs, patterns, and constraints. Prefer the mobjects, "
        "animations, and helpers shown here, and respect the stated gotchas:\n\n"
        "<manim_reference>\n" + MANIM_REFERENCE + "\n</manim_reference>"
    )
    if MANIM_REFERENCE
    else ""
)

_CODEGEN_OUTPUT_FORMAT = (
    "Respond with ONLY the complete, runnable Python script as raw source code "
    "(a single file including all imports). Do NOT wrap it in markdown code fences, "
    "do NOT return JSON, and do NOT add any commentary before or after the code."
)

CODEGEN_SYSTEM_PROMPT = "\n\n".join(
    part for part in (_CODEGEN_REQUIREMENTS, _CODEGEN_REFERENCE, _CODEGEN_OUTPUT_FORMAT) if part.strip()
)

ALIGNMENT_SYSTEM_PROMPT = """You are a strict reviewer checking whether a Manim script faithfully
implements an educational plan for a chemistry concept.

You are given the concept, its intents, entities, scene_plan, and the candidate script.
Decide whether the script visually covers the intents and the key entities and broadly
follows the scene_plan. Minor stylistic differences are acceptable; missing core entities
or intents is not.

Respond with ONLY a JSON object of this exact shape:
{"aligned": true or false, "feedback": "specific, actionable notes on what to add or fix"}
If aligned is true, feedback may be empty. Strictly valid JSON only."""
