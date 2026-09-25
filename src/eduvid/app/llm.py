"""LLM inference via Amazon Bedrock using the boto3 SDK.

Inference goes through the Bedrock Runtime ``converse`` API on the real AWS
endpoint, authenticated with the Bedrock API key from ``config.json`` (exported
as the ``AWS_BEARER_TOKEN_BEDROCK`` bearer token). The public interface
(``chat`` / ``chat_json``) is unchanged so the workflow nodes need no edits.
"""
from __future__ import annotations

import json
import os
import re
import logging
from functools import lru_cache
from typing import Any

import boto3

from .config import get_llm_config


@lru_cache(maxsize=1)
def get_client():
    """Build a cached Bedrock Runtime client authenticated via the API key."""
    cfg = get_llm_config()
    # The Bedrock API key is consumed by botocore as a bearer token.
    if os.getenv("AWS_API_KEY"):
        print("AWS API KEY available")
    logging.info(f"env AWS API KEY: {os.getenv("AWS_API_KEY")}")
    logging.info(f"env AWS MODEL: {os.getenv("AWS_MODEL")}")
    logging.info(f"AWS MODEL: {cfg.model}")
    logging.info(f"REGION: {cfg.region}")
    os.environ["AWS_BEARER_TOKEN_BEDROCK"] = os.getenv("AWS_API_KEY")
    return boto3.client("bedrock-runtime", region_name=cfg.region)


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
    cfg = get_llm_config()
    system, converse_messages = _to_converse(messages)

    kwargs: dict[str, Any] = {
        "modelId": cfg.model,
        "messages": converse_messages,
        "inferenceConfig": {"maxTokens": max_tokens, "temperature": temperature},
    }
    if system:
        kwargs["system"] = system

    response = get_client().converse(**kwargs)
    blocks = response["output"]["message"]["content"]
    return "".join(block.get("text", "") for block in blocks)


_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def _extract_json_text(text: str) -> str:
    """Pull a JSON object out of a possibly fenced / chatty response."""
    fenced = _JSON_FENCE.search(text)
    if fenced:
        return fenced.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1].strip()
    return text.strip()


def chat_json(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.0,
    max_tokens: int = 4096,
) -> dict[str, Any]:
    """Run a chat completion and parse the assistant content as JSON."""
    raw = chat(messages, temperature=temperature, max_tokens=max_tokens)
    candidate = _extract_json_text(raw)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM did not return valid JSON: {exc}\nRaw output:\n{raw}") from exc
