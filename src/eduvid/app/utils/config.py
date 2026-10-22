"""Load LLM and workflow configuration."""
from __future__ import annotations

import os
import json
import boto3
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

MAX_ANSWER_RETRIES = 6
MAX_AGENT_RETRIES = 6


def get_secret_dict(secret_name: str):
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
        "appsync_realtime": all_secrets["APPSYNC_REALTIME"],
        "e2b_api_key": all_secrets["E2B_API_KEY"]
    }

    return all_secrets

load_dotenv(find_dotenv())
all_secrets = get_all_secrets(os.environ.get("SECRET_STORE_NAME"))