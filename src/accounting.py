"""Cost aggregation refuses incomplete evidence and normalises currencies explicitly."""

from __future__ import annotations
import math
from src.costs import cost_per_1k_predictions

COMPONENTS = {"training", "storage", "serving", "pipeline", "monitoring", "llm"}


def billing_total(records, usd_thb):
    if not records:
        raise ValueError("No billing evidence; unavailable is not zero spend")
    if not math.isfinite(usd_thb) or usd_thb <= 0:
        raise ValueError("Positive dated exchange rate required")
    totals = {name: 0.0 for name in COMPONENTS}
    for record in records:
        if record["component"] not in COMPONENTS:
            raise ValueError("Unclassified billed component")
        if record.get("course") != "itcs355" or str(record.get("lab")) != "5":
            raise ValueError("Billing record is not scoped to Lab 5")
        amount = record["amount"]
        if not math.isfinite(amount):
            raise ValueError("Nonfinite billed amount")
        currency = record["currency"]
        if currency not in ("THB", "USD"):
            raise ValueError("Unsupported currency; supply verified conversion")
        totals[record["component"]] += amount * (usd_thb if currency == "USD" else 1)
    return totals


def compute_scenarios(hourly_thb, throughput_rps):
    if not math.isfinite(hourly_thb) or hourly_thb < 0:
        raise ValueError("Invalid hourly rate")
    return {
        str(int(u * 100)): cost_per_1k_predictions(hourly_thb, throughput_rps, u)
        for u in (0.05, 0.25, 0.8)
    }
