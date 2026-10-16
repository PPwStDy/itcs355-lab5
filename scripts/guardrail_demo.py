"""Replay an authored injection failure and show the deterministic control firing."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.triage import enforce, validate_output


def main():
    cases = [json.loads(x) for x in Path("evals/golden/maintenance.jsonl").read_text().splitlines()]
    responses = [
        json.loads(x)
        for x in Path("evals/fixtures/maintenance-regressed.jsonl").read_text().splitlines()
    ]
    case = next(x for x in cases if x["category"] == "injection")
    raw = next(x["response"] for x in responses if x["id"] == case["id"])
    safe, violations = enforce(case["inputs"], raw)
    assert violations and not validate_output(case["inputs"], json.dumps(safe))
    report = dict(
        case_id=case["id"],
        raw=json.loads(raw),
        violations=violations,
        controlled=safe,
        provenance="replayed synthetic failure; no live model or tool call",
    )
    path = Path("reports/evidence/guardrail-demo.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
