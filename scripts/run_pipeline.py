"""Run portable pipeline stages locally, with explicitly simulated registration/deployment."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cloudlayer.local import LabAdapter
from src import config
from src.workflow import run


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=Path("data/raw/sensors.csv"))
    ap.add_argument("--out", type=Path, default=Path("reports/local-pipeline"))
    ap.add_argument("--incumbent", type=float)
    ap.add_argument("--bootstrap", action="store_true")
    args = ap.parse_args()
    result = run(
        args.source,
        args.out,
        LabAdapter(config.load(strict=False)),
        incumbent=args.incumbent,
        bootstrap=args.bootstrap,
    )
    print(("GATE PASS: " if result.passed else "GATE FAIL: ") + result.reason)
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
