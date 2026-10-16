"""Token arithmetic requires explicit verified prices and provider-reported usage."""

from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Usage:
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int = 0
    cache_write_tokens: int = 0

    def __post_init__(self):
        values = (
            self.input_tokens,
            self.output_tokens,
            self.cached_input_tokens,
            self.cache_write_tokens,
        )
        if any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in values):
            raise ValueError("Token counts must be nonnegative provider-reported integers")
        if self.cached_input_tokens + self.cache_write_tokens > self.input_tokens:
            raise ValueError("Cached and written tokens must be disjoint subsets of input_tokens")


@dataclass(frozen=True)
class Prices:
    input_per_million_thb: float
    output_per_million_thb: float
    cached_read_per_million_thb: float
    cache_write_per_million_thb: float
    source_url: str
    verified_at: str
    model: str
    region: str

    def __post_init__(self):
        values = (
            self.input_per_million_thb,
            self.output_per_million_thb,
            self.cached_read_per_million_thb,
            self.cache_write_per_million_thb,
        )
        if (
            any(not math.isfinite(v) or v < 0 for v in values)
            or not self.source_url
            or not self.verified_at
        ):
            raise ValueError("Finite nonnegative rates and dated source evidence are required")


def request_cost(prices: Prices, usage: Usage):
    fresh = usage.input_tokens - usage.cached_input_tokens - usage.cache_write_tokens
    return (
        fresh * prices.input_per_million_thb
        + usage.output_tokens * prices.output_per_million_thb
        + usage.cached_input_tokens * prices.cached_read_per_million_thb
        + usage.cache_write_tokens * prices.cache_write_per_million_thb
    ) / 1_000_000


def cost_per_1k_requests(prices, usage):
    return request_cost(prices, usage) * 1000


def output_cap_saving(prices, before: Usage, after: Usage):
    # Uses two actual measured runs; a max-token setting is not observed output usage.
    return cost_per_1k_requests(prices, before) - cost_per_1k_requests(prices, after)


def cache_breakeven_hit_rate(prices):
    saving = prices.input_per_million_thb - prices.cached_read_per_million_thb
    extra = max(0, prices.cache_write_per_million_thb - prices.input_per_million_thb)
    if saving <= 0:
        return None
    return extra / (saving + extra)


def measured_usage(record):
    if record.get("provenance") != "provider_response" or not isinstance(
        record.get("provider_usage"), dict
    ):
        raise ValueError(
            "A provider usage receipt is required; authored fixtures cannot establish token cost"
        )
    raw = record["provider_usage"]
    if "cached_input_tokens" not in raw:
        raise ValueError(
            "Provider cache counters are unavailable; cannot claim a measured cache hit rate"
        )
    receipt = record.get("raw_provider_usage")
    if not isinstance(receipt, dict):
        raise ValueError("Original provider usage fields are required")
    if raw["input_tokens"] != receipt.get("prompt_tokens") or raw["output_tokens"] != receipt.get(
        "completion_tokens"
    ):
        raise ValueError("Normalized counts differ from the original provider receipt")
    if raw["cached_input_tokens"] != (receipt.get("prompt_tokens_details") or {}).get(
        "cached_tokens"
    ):
        raise ValueError("Cache counts differ from the original provider receipt")
    return Usage(
        input_tokens=raw["input_tokens"],
        output_tokens=raw["output_tokens"],
        cached_input_tokens=raw.get("cached_input_tokens", 0),
        cache_write_tokens=raw.get("cache_write_tokens", 0),
    )
