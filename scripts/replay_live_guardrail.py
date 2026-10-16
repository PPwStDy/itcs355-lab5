"""Replay a captured provider failure through the current guardrail, without cloud calls."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.triage import enforce, expected

root = Path(__file__).resolve().parents[1]
case_id = "maintenance-injection"
golden = [json.loads(x) for x in (root / "evals/golden/maintenance.jsonl").read_text().splitlines()]
rows = [
    json.loads(x)
    for x in (root / "reports/evidence/live-v2-changed.jsonl").read_text().splitlines()
]
case = next(x for x in golden if x["id"] == case_id)
row = next(x for x in rows if x["id"] == case_id)
assert row["provenance"] == "provider_response"
safe, failures = enforce(case["inputs"], row["response"])
assert failures and safe["decision"] == expected(case["inputs"])
print(
    json.dumps(
        dict(
            case=case_id,
            provider_request_id=row["request_id"],
            failures=failures,
            safe_response=safe,
            cloud_call_made=False,
        ),
        indent=2,
    )
)
