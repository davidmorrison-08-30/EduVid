"""LLM inference via Amazon Bedrock using the boto3 SDK.

Inference goes through the Bedrock Runtime ``converse`` API on the real AWS
endpoint, authenticated with the Bedrock API key from ``config.json`` (exported
as the ``AWS_BEARER_TOKEN_BEDROCK`` bearer token). The public interface
"""
from __future__ import annotations
import json
import os
import re
import logging
from functools import lru_cache
from typing import Any
import boto3
from botocore.config import Config

from .config import all_secrets

def get_client():
    """Build a cached Bedrock Runtime client authenticated via the API key."""
    os.environ["AWS_BEARER_TOKEN_BEDROCK"] = all_secrets["bedrock_token"]
    custom_config = Config(
        connect_timeout=15,    
        read_timeout=3600,       
        retries={
            'max_attempts': 9999, 
            'mode': 'standard' 
        }
    )
    return boto3.client("bedrock-runtime", region_name=all_secrets["region"], config=custom_config)


def _to_converse(messages: list[dict[str, str]]) -> tuple[list[dict], list[dict]]:
    """Split OpenAI-style messages into Bedrock ``system`` and ``messages``."""
    system: list[dict] = []
    converse_messages: list[dict] = []
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        if role == "system":
            system.append({"text": content})
        else:
            converse_messages.append(
                {
                    "role": "assistant" if role == "assistant" else "user",
                    "content": [{"text": content}],
                }
            )
    return system, converse_messages


def chat(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.0,
    max_tokens: int = 4096,
) -> str:
    """Run a Bedrock converse call and return the assistant text content."""

    system, converse_messages = _to_converse(messages)

    kwargs: dict[str, Any] = {
        "modelId": all_secrets["model"],
        "messages": converse_messages,
        "inferenceConfig": {"temperature": temperature},
        "additionalModelRequestFields": {
            "reasoning": {"effort": "low"}
        }
    }
    if system:
        kwargs["system"] = system

    response = get_client().converse(**kwargs)
    blocks = response["output"]["message"]["content"]
    return "".join(block.get("text", "") for block in blocks)




