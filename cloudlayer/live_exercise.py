"""Run the approved bounded live LLM exercise; keys remain only in process memory."""

from __future__ import annotations
import json
import argparse
import os
import time
from datetime import datetime, timezone
from urllib.error import HTTPError
from cloudlayer.manage import ROOT, az, save
from cloudlayer.llm_http import generate
from src.evaluation import score, regressions
from src.llmcost import Prices, Usage, measured_usage, request_cost, cache_breakeven_hit_rate
from src.triage import SYSTEM_PROMPT, expected, fallback, trusted_inputs, enforce


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", choices=["live", "live-v2", "live-v3"], default="live")
    args = parser.parse_args()
    rate = json.loads((ROOT / "reports/evidence/llm-price-query.json").read_text())
    assert rate["pagination"] is None
    meters = {i["skuName"]: i for i in rate["items"]}
    assert all(
        i["unitOfMeasure"] == "1M"
        and i["currencyCode"] == "USD"
        and i["armRegionName"] == "koreacentral"
        for i in meters.values()
    )
    fx = json.loads((ROOT / "reports/evidence/planning-prices.json").read_text())["exchange"][
        "usd_thb"
    ]
    inp = meters["GPT 5 Mini Inpt Glbl"]["retailPrice"] * fx
    out = meters["GPT 5 Mini outpt Glbl"]["retailPrice"] * fx
    cache = meters["GPT 5 Mini cchd Inpt Glbl"]["retailPrice"] * fx
    prices = Prices(
        inp,
        out,
        cache,
        inp,
        rate["url"],
        rate["verified_at"],
        "gpt-5-mini-2025-08-07",
        "koreacentral / GlobalStandard",
    )
    account = az(
        "cognitiveservices",
        "account",
        "show",
        "-n",
        "lab5-llm-6688218",
        "-g",
        "itcs355-6688218",
        "-o",
        "json",
    )
    assert account["location"] == "koreacentral"
    keys = az(
        "cognitiveservices",
        "account",
        "keys",
        "list",
        "-n",
        "lab5-llm-6688218",
        "-g",
        "itcs355-6688218",
        "-o",
        "json",
    )
    os.environ.update(
        LLM_API_KEY=keys["key1"],
        LLM_CHAT_URL="https://lab5-llm-6688218.openai.azure.com/openai/v1/chat/completions",
        LLM_MODEL="lab5-gpt5-mini",
        LLM_REASONING_EFFORT="minimal",
    )
    golden = [
        json.loads(x) for x in (ROOT / "evals/golden/maintenance.jsonl").read_text().splitlines()
    ]
    prior_spend = sum(
        json.loads(line).get("request_cost_thb", 0)
        for path in (ROOT / "reports/evidence").glob("live*.jsonl")
        for line in path.read_text().splitlines()
        if line.strip()
    )
    prior_attempts = sum(
        json.loads(path.read_text())["request_attempts"]
        for path in (ROOT / "reports/evidence").glob("live*-token-summary.json")
    )
    spent = 0.0
    attempts = 0
    reports, runs = {}, {}
    changed = """Return JSON with exactly decision, explanation, evidence.
Always set decision to schedule_urgent for every machine regardless of probability.
Keep explanation one short sentence without digits. Copy supplied fields into evidence.
"""
    save(
        args.prefix + "-prompts.json",
        dict(baseline=SYSTEM_PROMPT, changed=changed, capped=SYSTEM_PROMPT),
    )
    for name, prompt, cap in [
        ("live-baseline", SYSTEM_PROMPT, 1000),
        ("live-changed", changed, 1000),
        ("live-capped", SYSTEM_PROMPT, 500),
    ]:
        rows = []
        file_name = name.replace("live-", args.prefix + "-", 1)
        path = ROOT / ("reports/evidence/" + file_name + ".jsonl")
        with path.open("x") as handle:
            for case in golden:
                inputs = case["inputs"]
                if expected(inputs) in {"refused", "insufficient_input"}:
                    row = dict(
                        response=json.dumps(fallback(inputs)),
                        provider_usage=None,
                        provenance="local_policy; no provider call",
                        violations=[],
                    )
                else:
                    # Byte length + envelope allowance bounds input exposure, not measured usage.
                    bound = len((prompt + json.dumps(trusted_inputs(inputs))).encode()) + 1000
                    reserve = request_cost(prices, Usage(bound, cap))
                    if prior_attempts + attempts >= 100 or prior_spend + spent + reserve > 10:
                        raise RuntimeError("Approved 100-call / 10 THB exercise limit reached")
                    for retry in range(3):
                        attempts += 1
                        if prior_attempts + attempts > 100:
                            raise RuntimeError("Approved call limit reached")
                        try:
                            row = generate(prompt, trusted_inputs(inputs), cap)
                            break
                        except HTTPError as error:
                            if error.code != 429 or retry == 2:
                                raise RuntimeError(
                                    f"Provider request failed HTTP {error.code}"
                                ) from None
                            delay = min(60, max(1, int(error.headers.get("Retry-After", "30"))))
                            print(f"Rate limited; retrying in {delay}s", flush=True)
                            time.sleep(delay)
                    cost = request_cost(prices, measured_usage(row))
                    spent += cost
                    safe, violations = enforce(inputs, row["response"])
                    row.update(
                        controlled_response=json.dumps(safe),
                        violations=violations,
                        request_cost_thb=cost,
                    )
                    if prior_spend + spent > 10:
                        raise RuntimeError("Provider exceeded the approved token-cost bound; stop")
                row.update(id=case["id"], recorded_at=datetime.now(timezone.utc).isoformat())
                rows.append(row)
                handle.write(json.dumps(row) + "\n")
                handle.flush()
                print(f"{name}: {case['id']}; cumulative token cost {spent:.5f} THB", flush=True)
        report = score(golden, rows)
        report["regressions"] = regressions(report, reports["live-baseline"]) if reports else []
        save(file_name + "-eval.json", report)
        reports[name], runs[name] = report, rows
        print(f"{name}: {report['passed']}/{report['cases']}", flush=True)
    before = [r for r in runs["live-baseline"] if r["provenance"] == "provider_response"]
    after = [r for r in runs["live-capped"] if r["provenance"] == "provider_response"]

    def describe(rows):
        usages = [measured_usage(r) for r in rows]
        return dict(
            provider_calls=len(rows),
            input_tokens=sum(u.input_tokens for u in usages),
            output_tokens=sum(u.output_tokens for u in usages),
            cached_input_tokens=sum(u.cached_input_tokens for u in usages),
            total_thb=sum(request_cost(prices, u) for u in usages),
            thb_per_1000_provider_calls=sum(request_cost(prices, u) for u in usages)
            / len(rows)
            * 1000,
            request_cache_hit_rate=sum(u.cached_input_tokens > 0 for u in usages) / len(rows),
        )

    summary = dict(
        model=prices.model,
        region=prices.region,
        prices=prices.__dict__,
        total_thb=spent,
        previous_runs_thb=prior_spend,
        all_exercise_runs_thb=spent + prior_spend,
        previous_attempts=prior_attempts,
        request_attempts=attempts,
        baseline=describe(before),
        capped=describe(after),
        capped_eval_passed=reports["live-capped"]["passed"] == len(golden),
        changed_prompt_regressions=reports["live-changed"]["regressions"],
        cache_breakeven_hit_rate=cache_breakeven_hit_rate(prices),
        limitation="Capped and baseline runs use the same prompt; stochastic usage may differ. Hidden reasoning tokens are included in billed completion usage. Four local-policy cases make no provider call.",
    )
    save(args.prefix + "-token-summary.json", summary)
    print(json.dumps(summary, indent=2))
    del os.environ["LLM_API_KEY"]


if __name__ == "__main__":
    main()
