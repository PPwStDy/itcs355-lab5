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

Required evidence still depends on actual completion: end-to-end managed success; the named evaluation failure with register/deploy absent; the real revoked-permission 403 and restoration; measured optimisation; final Lab 5 billing; provider-console teardown screenshot; a real second-provider round trip/invocation; live LLM/prompt/capped runs with provider usage. No AWS/GCP credentials or pay-as-you-go Azure OpenAI quota were available during setup.
