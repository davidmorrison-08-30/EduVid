"""Load LLM and workflow configuration."""
from __future__ import annotations

import os
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "outputs"

# Workflow iteration caps.
MAX_ALIGNMENT_RETRIES = 5
MAX_CODEGEN_RETRIES = 5
# Hard ceiling on render wall-clock time (seconds).
RENDER_TIMEOUT_SECONDS = 360


@dataclass(frozen=True)
class LLMConfig:
    api_key: str
    region: str
    model: str


@lru_cache(maxsize=1)
def get_llm_config() -> LLMConfig:
    """Read the Amazon Bedrock LLM settings from config.json."""
    return LLMConfig(
        api_key=os.getenv("AWS_API_KEY"),
        region=os.getenv("AWS_REGION"),
        model=os.getenv("AWS_MODEL"),
    )
