"""Chat-completion transport: preserve the provider receipt, never count words as tokens."""

from __future__ import annotations
import hashlib
import json
import os
import time
import urllib.request


def generate(system, inputs, max_output_tokens):
    url = os.environ["LLM_CHAT_URL"]
    key = os.environ["LLM_API_KEY"]
    if not url.startswith("https://"):
        raise ValueError("Use an HTTPS provider endpoint")
    payload = dict(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(inputs)},
        ],
        max_tokens=max_output_tokens,
        temperature=0,
        response_format={"type": "json_object"},
    )
    reasoning_effort = os.environ.get("LLM_REASONING_EFFORT")
    if reasoning_effort:
        # Reasoning chat models include hidden reasoning in this completion cap.
        payload["max_completion_tokens"] = payload.pop("max_tokens")
        payload.pop("temperature")
        payload["reasoning_effort"] = reasoning_effort
    if os.environ.get("LLM_MODEL"):
        payload["model"] = os.environ["LLM_MODEL"]
    header = os.environ.get("LLM_AUTH_HEADER", "api-key")
    credential = ("Bearer " + key) if header.lower() == "authorization" else key
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", header: credential},
    )
    start = time.perf_counter()
    with urllib.request.urlopen(req, timeout=60) as response:
        body = json.load(response)
    raw = body["usage"]
    if "prompt_tokens" not in raw or "completion_tokens" not in raw:
        raise ValueError("Provider response lacks required usage fields")
    usage = dict(
        input_tokens=raw["prompt_tokens"],
        output_tokens=raw["completion_tokens"],
        cache_write_tokens=0,
    )
    details = raw.get("prompt_tokens_details") or {}
    if "cached_tokens" in details:
        usage["cached_input_tokens"] = details["cached_tokens"]
    return dict(
        response=body["choices"][0]["message"]["content"],
        provider_usage=usage,
        raw_provider_usage=raw,
        model=body.get("model"),
        request_id=body.get("id"),
        latency_ms=round((time.perf_counter() - start) * 1000, 2),
        provenance="provider_response",
        prompt_sha256=hashlib.sha256(system.encode()).hexdigest(),
        max_output_tokens=max_output_tokens,
        reasoning_effort=reasoning_effort,
        finish_reason=body["choices"][0].get("finish_reason"),
    )
