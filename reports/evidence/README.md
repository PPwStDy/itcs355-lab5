# Lab 5 captured evidence

This folder contains only captured results and explicitly labelled offline demonstrations.

- Pre-run forecast commit: c3b7231; planning-prices.json retains the exact VM retail item and dated ECB exchange calculation.
- pre-run-course-billing.json is the course spend before Lab 5, not this lab's actual bill.
- container-build.json records successful Azure ACR build ck1 and its digest.
- identity-assignments.json records the three isolated identities and scoped grants.
- managed-run.json and managed-rejected-run.json link to actual submitted Azure ML runs. Check their latest status files for actual stage completion; submission alone is not success.
- schedule.json records the actual enabled weekly retraining schedule; it is removed after the exercise.
- llm-baseline.json, llm-regressed.json and guardrail-demo.json are authored-fixture/control checks, not live provider responses.
- local verification and native pipeline schema checks are distinct from managed execution.

The actual rejected managed run stopped at evaluation; managed-gate-proof.json verifies that register/deploy were not started, and managed-gate-rejection.txt retains the failure. The permission drill returned a real HTTP 403 and restored the exact removed Reader grant; see permission-exercise.json and permission-denied.txt.

The restored Reader grant also passed an actual managed read check on a fresh node; see permission-restoration-check.json and permission-restored.txt. optimisation.json records an observed idle-node count of 1 to 0 in 177.33 seconds, priced at 7.1776 THB/hour of avoided idle capacity, not final invoice savings.

Live LLM evidence is captured separately from authored fixtures. live-baseline.jsonl / live-changed.jsonl / live-capped.jsonl preserve the first attempt, including its 10/14 and 12/14 failures. live-v2-* records the clarified prompt: baseline 13/14; deliberately faulty prompt 6/14 with seven regressions; capped clarified candidate 14/14. live-gate-command.json records expected command exit codes 1 and 0. live-guardrail-proof.json and scripts/replay_live_guardrail.py demonstrate a real captured faulty-prompt output blocked by validation. Notes were excluded, so this is not labelled a successful prompt injection.

The exact Microsoft retail token meters are in llm-price-query.json. All 60 successful calls cost 0.3922373697 THB using provider-reported usage, with four rate-limit retries. The capped run did not reduce observed cost; live-v2-token-summary.json retains that result. All cache counters were zero. The temporary Korea Central LLM account and deployment were removed; llm-cleanup.json verifies no active account remains. The earlier Southeast Asia policy rejection remains in separate evidence.

The full managed run stoic_river_3l9pd2rtlf completed all six stages. managed-success.json retains the actual stage IDs, gate, metrics, code lineage and registered/deployed model. managed-pipeline-completed.jpg is the actual Azure ML console graph. endpoint-benchmark.json contains 25 actual measured request latencies after five warm-ups, with the expected model on every response. The successful initializer logs prove the manifest-only conditional reader resolved startup; no account-wide reader was granted.

Still required before claiming full completion: final Lab 5 billing/allocation; a real second-provider round trip/invocation. AWS/GCP access has not been established.

Teardown completed and an independent read-only check returned empty Lab 5 endpoints, computes, schedules, identities, active_jobs and llm_accounts. cleanup-protection-proof.json confirms the exact conditional manifest grant returns RoleAssignmentNotFound and the existing workspace, storage, registry and shared zero-node cluster remain. The next-day read-only follow-up is recorded in billing-followup.json.
