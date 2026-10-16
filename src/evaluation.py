"""Per-case gate rejects regressions, missing cases, duplicate IDs and changed golden sets."""

from __future__ import annotations
import hashlib
import json
from src.triage import validate_output


def unique(rows, label):
    ids = [row["id"] for row in rows]
    if not rows or len(ids) != len(set(ids)):
        raise ValueError(f"{label}: empty set or duplicate IDs")
    return {row["id"]: row for row in rows}


def score(golden, responses):
    unique(golden, "golden")
    recorded = unique(responses, "responses")
    results = []
    for case in golden:
        row = recorded.get(case["id"])
        failures = (
            ["no response recorded"]
            if row is None
            else validate_output(case["inputs"], row["response"])
        )
        if row is not None:
            try:
                if json.loads(row["response"]).get("decision") != case["expected_decision"]:
                    failures.append(
                        "decision differs from independently specified golden expectation"
                    )
            except (ValueError, AttributeError):
                pass
        results.append(dict(id=case["id"], passed=not failures, failures=failures))
    canonical = json.dumps(golden, sort_keys=True, separators=(",", ":")).encode()
    return dict(
        cases=len(results),
        passed=sum(r["passed"] for r in results),
        results=results,
        golden_sha256=hashlib.sha256(canonical).hexdigest(),
        usage_provenance=sorted(set(str(r.get("provenance", "unknown")) for r in responses)),
    )


def regressions(report, baseline):
    if report["golden_sha256"] != baseline["golden_sha256"]:
        raise ValueError("Golden set changed; review and record a new baseline explicitly")
    before = {r["id"]: r["passed"] for r in baseline["results"]}
    now = {r["id"]: r["passed"] for r in report["results"]}
    return sorted(cid for cid, passed in before.items() if passed and not now.get(cid, False))
