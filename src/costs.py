"""Cost model. Used by Labs 2, 3, and 5.

Prices change and differ by region, so these are STARTING VALUES you must verify against
your provider's calculator. Verifying them is part of Lab 2; citing a stale number without
checking is the kind of thing the cost report is designed to catch.

Legacy lookup rates are THB per hour. SPOT_FACTOR is a tutorial assumption,
not a verified current discount. Lab 5 accounting uses captured regional retail prices
and actual usage receipts instead of this legacy tuning lookup.
"""

from __future__ import annotations

import json
from src import config


def price_table():
    """Legacy tutorial rates; Lab 5 accounting uses separately verified receipts."""
    return json.loads(config.cost_rate_file().read_text())


SPOT_FACTOR = 0.30
DEFAULT_UTILISATIONS = (0.05, 0.25, 0.80)


def hourly_rate(provider: str, instance: str, spot: bool = False) -> float:
    table = price_table().get(provider.lower())
    if table is None:
        raise KeyError(
            f"No price table for provider {provider!r}. Configure COST_RATE_FILE with verified rates."
        )
    if instance not in table:
        raise KeyError(
            f"No rate for {instance!r} on {provider}. Known: {sorted(table)}. "
            "Add the instance you actually used — do not substitute a similar one silently."
        )
    return table[instance] * (SPOT_FACTOR if spot else 1.0)


def cost_per_1k_predictions(
    hourly_thb: float,
    throughput_rps: float,
    utilisation: float,
) -> float:
    """Cost of 1,000 predictions on an always-on endpoint.

    utilisation is the fraction of provisioned capacity you actually use. It is the most
    fragile number in any serving cost estimate, which is why Lab 3 makes you state it
    explicitly and Lab 5 makes you report three of them.
    """
    if not 0 < utilisation <= 1:
        raise ValueError("utilisation must be in (0, 1]")
    if throughput_rps <= 0:
        raise ValueError("throughput_rps must be positive")
    effective_rps = throughput_rps * utilisation
    seconds_per_1k = 1000.0 / effective_rps
    return hourly_thb * (seconds_per_1k / 3600.0)


def batch_breakeven_rps(
    endpoint_hourly_thb: float,
    batch_job_thb: float,
    batch_runs_per_day: int = 1,
) -> float:
    """Request rate below which scheduled batch inference is cheaper than a warm endpoint.

    Lab 3 asks you to compute this for your own service. The answer is usually lower than
    students expect, which is the point.
    """
    endpoint_daily = endpoint_hourly_thb * 24
    batch_daily = batch_job_thb * batch_runs_per_day
    if batch_daily >= endpoint_daily:
        return 0.0
    return (endpoint_daily - batch_daily) / 86400.0
