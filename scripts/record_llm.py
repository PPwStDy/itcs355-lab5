"""Record a live baseline/changed/capped prompt run, with exact usage receipts."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cloudlayer.llm_http import generate
from src.triage import SYSTEM_PROMPT, enforce, expected, fallback, trusted_inputs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", type=Path, default=Path("evals/golden/maintenance.jsonl"))
    ap.add_argument("--prompt-file", type=Path)
    ap.add_argument("--max-output-tokens", type=int, default=200)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if not 32 <= args.max_output_tokens <= 1000:
        raise ValueError("Output cap must be between 32 and 1000 tokens")
    prompt = args.prompt_file.read_text() if args.prompt_file else SYSTEM_PROMPT
    cases = [json.loads(x) for x in args.golden.read_text().splitlines() if x.strip()]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as handle:
        for case in cases:
            inputs = case["inputs"]
            if expected(inputs) in ("refused", "insufficient_input"):
                row = dict(
                    response=json.dumps(fallback(inputs)),
                    provider_usage=None,
                    provenance="local_policy; no provider call",
                    violations=[],
                )
            else:
                row = generate(prompt, trusted_inputs(inputs), args.max_output_tokens)
                safe, violations = enforce(inputs, row["response"])
                row.update(controlled_response=json.dumps(safe), violations=violations)
            row.update(id=case["id"], recorded_at=datetime.now(timezone.utc).isoformat())
            handle.write(json.dumps(row) + "\n")
            handle.flush()
    print(
        f"Wrote provider receipts to {args.out}; evaluate raw responses before accepting a change"
    )


if __name__ == "__main__":
    main()
