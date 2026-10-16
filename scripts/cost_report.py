"""Generate a report from audited billing and usage receipts; reject placeholders."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.accounting import billing_total, compute_scenarios
from src.llmcost import Prices, cache_breakeven_hit_rate, measured_usage, request_cost


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("reports/lab5-cost.md"))
    args = ap.parse_args()
    evidence = json.loads(args.evidence.read_text())
    if (
        not evidence.get("billing_source")
        or not evidence.get("billing_period")
        or not evidence.get("exchange_rate_source")
    ):
        raise ValueError("Billing and dated exchange-rate source evidence required")
    totals = billing_total(evidence["billing_records"], evidence["usd_thb"])
    actual = sum(totals.values())
    estimate = evidence["estimate_thb"]
    if estimate <= 0 or not evidence.get("estimate_commit"):
        raise ValueError("Positive pre-run estimate and its prior commit required")
    scenarios = compute_scenarios(
        evidence["serving_hourly_thb"], evidence["measured_throughput_rps"]
    )
    optimisation = evidence["optimisation"]
    if not optimisation.get("before_evidence") or not optimisation.get("after_evidence"):
        raise ValueError("Applied optimisation needs measured before/after evidence")
    prices = Prices(**evidence["token_prices"])
    before = evidence["llm_before"]
    after = evidence["llm_after"]
    if not before or not after or not evidence["capped_eval_passed"]:
        raise ValueError("Two measured LLM runs and a passing capped eval are required")

    def per_1000(rows):
        return sum(request_cost(prices, measured_usage(row)) for row in rows) / len(rows) * 1000

    old, new = per_1000(before), per_1000(after)
    hits = sum(measured_usage(row).cached_input_tokens > 0 for row in after) / len(after)
    delta = actual - estimate
    text = (
        f"""# Lab 5 cost report

## 1. Estimate before running
{estimate:.2f} THB, committed in {evidence["estimate_commit"]}.

## 2. Actual billing
{actual:.2f} THB. Source: {evidence["billing_source"]}; period: {evidence["billing_period"]}.

## 3. Gap
{delta:+.2f} THB ({delta / estimate * 100:+.1f}%). {evidence["gap_explanation"]}
The within-20% comparison uses estimate as denominator; matching billing does not prove this forecast was accurate.

## 4. Components
"""
        + "\n".join(f"- {key}: {value:.4f} THB" for key, value in sorted(totals.items()))
        + f"""

## 5. Utilisation scenarios
Measured throughput: {evidence["measured_throughput_rps"]} req/s.
"""
        + "\n".join(
            f"- {key}% utilisation: {value:.4f} THB/1,000 predictions"
            for key, value in scenarios.items()
        )
        + f"""

## 6. Applied optimisation
{optimisation["description"]}
Before: {optimisation["before_evidence"]}. After: {optimisation["after_evidence"]}.

## 7. Token bill and budget defence
{len(before)} provider calls before, {len(after)} provider calls after.
Before: {old:.4f} THB/1,000 requests; after: {new:.4f}; saving: {old - new:.4f}.
Working: sum(fresh_input*input_rate + output*output_rate + cached_input*cached_rate + cache_write*write_rate) / 1,000,000 / calls * 1,000.
Cache break-even hit fraction: {cache_breakeven_hit_rate(prices)}; measured request hit fraction: {hits:.4f}.
Prices: {prices.source_url}; verified {prices.verified_at}; model {prices.model}; region {prices.region}.
The capped run must pass the same golden-set gate; cap changes alone do not establish savings.
{evidence["budget_defence"]}
"""
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text)
    print(f"Wrote {args.out}; actual={actual:.2f} THB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
