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


def get_secret_dict(secret_name: str):

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name="us-east-1"
    )

    get_secret_value_response = client.get_secret_value(
        SecretId=secret_name
    )

    secret_json = get_secret_value_response['SecretString']
    return json.loads(secret_json)


def get_all_secrets(secret_name: str) -> LLMConfig:
    """Read the Amazon Bedrock LLM settings from config.json."""
    all_secrets = get_secret_dict(secret_name)
    all_secrets = {
        "bedrock_token": all_secrets["AWS_BEARER_TOKEN_BEDROCK"],
        "region": all_secrets["AWS_REGION"],
        "model": all_secrets["AWS_MODEL"],
        "appsync_key": all_secrets["APPSYNC_API_KEY"],
        "appsync_graphql": all_secrets["APPSYNC_GRAPHQL"],
        "appsync_realtime": all_secrets["APPSYNC_REALTIME"]
    }

    return all_secrets

all_secrets = get_all_secrets("eduvid-secrets")