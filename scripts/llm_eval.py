"""Score the 14-case maintenance set; fixtures never generate a token bill."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.evaluation import regressions, score


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", type=Path, default=Path("evals/golden/maintenance.jsonl"))
    ap.add_argument(
        "--responses", type=Path, default=Path("evals/fixtures/maintenance-baseline.jsonl")
    )
    ap.add_argument("--out", type=Path, default=Path("reports/evidence/llm-baseline.json"))
    ap.add_argument("--baseline", type=Path)
    args = ap.parse_args()
    report = score(read(args.golden), read(args.responses))
    failed = [r["id"] for r in report["results"] if not r["passed"]]
    changed = regressions(report, json.loads(args.baseline.read_text())) if args.baseline else []
    report["regressions"] = changed
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"{report['passed']}/{report['cases']} cases passed")
    if failed or changed:
        print("GATE FAILED: " + ", ".join(changed or failed))
        return 1
    print("GATE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
