# Lab 5 maintenance evaluation

The canonical set is golden/maintenance.jsonl: 14 machine-maintenance cases, including grounding, safety refusal, injection and insufficient input. Each case states its expected decision independently of the implementation.

fixtures/maintenance-baseline.jsonl and maintenance-regressed.jsonl are authored fixtures with usage=null. They are test data, not recorded model calls. The baseline passes 14 cases; the degraded fixture fails injection, invented vibration and unsafe interlock advice. make llm-gate must exit nonzero.

Use scripts/record_llm.py for an actual configured provider. It preserves raw usage, model/request IDs, prompt hash and cap. Live receipts belong in reports/evidence and must never contain API keys. Built-in policy refusals have explicit local provenance and no provider usage.
