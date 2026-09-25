"""Load LLM and workflow configuration."""
from __future__ import annotations

import os
import json
import boto3
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "outputs"

# Workflow iteration caps.
MAX_ALIGNMENT_RETRIES = 5
MAX_CODEGEN_RETRIES = 5
# Hard ceiling on render wall-clock time (seconds).
RENDER_TIMEOUT_SECONDS = 360


@dataclass(frozen=True)
class LLMConfig:
    bedrock_token: str
    region: str
    model: str


def get_secret(secret_key: str):

    secret_name = secret_key

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name="us-east-1"
    )

    get_secret_value_response = client.get_secret_value(
        SecretId=secret_name
    )

    secret = get_secret_value_response['SecretString']
    return secret


@lru_cache(maxsize=1)
def get_llm_config() -> LLMConfig:
    """Read the Amazon Bedrock LLM settings from config.json."""
    return LLMConfig(
        bedrock_token=get_secret("AWS_BEARER_TOKEN_BEDROCK"),
        region=get_secret("AWS_REGION"),
        model=get_secret("AWS_MODEL"),
    )
