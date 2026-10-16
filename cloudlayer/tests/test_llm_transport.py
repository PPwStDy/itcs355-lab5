"""Verify model-compatible caps while retaining the original usage receipt."""

import io
import json
from cloudlayer.llm_http import generate


def test_reasoning_transport_keeps_actual_receipt(monkeypatch):
    monkeypatch.setenv("LLM_CHAT_URL", "https://example.invalid/chat/completions")
    monkeypatch.setenv("LLM_API_KEY", "test-only")
    monkeypatch.setenv("LLM_REASONING_EFFORT", "minimal")
    raw = {
        "prompt_tokens": 123,
        "completion_tokens": 81,
        "prompt_tokens_details": {"cached_tokens": 0},
        "completion_tokens_details": {"reasoning_tokens": 25},
    }

    def respond(request, timeout):
        payload = json.loads(request.data)
        assert payload["max_completion_tokens"] == 500
        assert "max_tokens" not in payload and "temperature" not in payload
        assert payload["reasoning_effort"] == "minimal"
        return io.BytesIO(
            json.dumps(
                {
                    "usage": raw,
                    "model": "test-model",
                    "id": "receipt-1",
                    "choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}],
                }
            ).encode()
        )

    monkeypatch.setattr("urllib.request.urlopen", respond)
    row = generate("Return JSON.", {"failure_probability": 0.3}, 500)
    assert row["raw_provider_usage"] == raw
    assert row["provider_usage"]["output_tokens"] == 81
    assert row["finish_reason"] == "stop"
