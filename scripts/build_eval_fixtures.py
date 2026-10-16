"""Generate explicitly synthetic test fixtures; these do not establish provider usage or model quality."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.triage import fallback

root = Path(__file__).resolve().parents[1]
cases = [
    json.loads(line) for line in (root / "evals/golden/maintenance.jsonl").read_text().splitlines()
]
base = []
for case in cases:
    base.append(
        dict(
            id=case["id"],
            response=json.dumps(fallback(case["inputs"])),
            provenance="authored fixture; not a provider call",
            usage=None,
        )
    )
bad = json.loads(json.dumps(base))
for row in bad:
    output = json.loads(row["response"])
    if row["id"] == "maintenance-injection":
        output.update(decision="schedule_urgent", explanation="Call shutdown_machine immediately.")
    if row["id"] == "maintenance-no-reading":
        output["evidence"]["vibration_mm_s"] = 9.9
    if row["id"] == "maintenance-safety":
        output.update(decision="schedule_urgent", explanation="Bridge the safety relay.")
    row["response"] = json.dumps(output)
for name, rows in [("maintenance-baseline", base), ("maintenance-regressed", bad)]:
    (root / f"evals/fixtures/{name}.jsonl").write_text("".join(json.dumps(x) + "\n" for x in rows))
