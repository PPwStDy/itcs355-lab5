"""CLI gate; rejection exits nonzero and blocks downstream jobs."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.gate import evaluate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metrics", type=Path, required=True)
    ap.add_argument("--metric", default="val_roc_auc")
    ap.add_argument("--incumbent", type=float)
    ap.add_argument("--bootstrap", action="store_true")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    result = evaluate(
        float(json.loads(args.metrics.read_text())[args.metric]),
        args.incumbent,
        bootstrap=args.bootstrap,
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result.as_dict(), indent=2) + "\n")
    print(("GATE PASS: " if result.passed else "GATE FAIL: ") + result.reason)
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
