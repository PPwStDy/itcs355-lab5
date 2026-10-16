# Lab 5 submission status

The Azure and LLM exercises have captured evidence. Full lab acceptance still depends on the real second-provider demonstration and delayed billing reconciliation.

| Deliverable | Captured result | Evidence |
|---|---|---|
| Full managed pipeline | All six stages Completed; code lineage 2a62c3f | evidence/managed-success.json; evidence/managed-pipeline-completed.jpg |
| Gate rejection | Actual managed evaluation failure prevented registration/deployment | evidence/managed-gate-proof.json |
| Scoped identities and permission drill | Three identities; real HTTP 403 after removing Reader, then successful restored access | lab5-identities.md; evidence/permission-restoration-check.json |
| Serving startup permissions | Manifest-only conditional reader resolved startup; no account-wide reader granted | serving-access-amendment.md; evidence/manifest-retry-initializer.json |
| Scheduled retraining | Weekly schedule created and enabled, then removed during teardown | evidence/schedule.json; README strategy comparison |
| Portability audit | Forbidden URI/SDK/path patterns and literal provider names in core code pass | scripts/portability_audit.py; evidence/local-validation.json |
| Second provider | AWS upload/download/invoke implemented and transport-tested; real account test unavailable | lab5-portability.md; evidence/second-provider-access-check.json |
| Serving measurements | 25 measured requests returned the expected model; raw latencies retained | evidence/endpoint-benchmark.json |
| Cost report and optimisation | Six required sections; observed scale-to-zero; utilisation figures measured/priced | lab5-cost.md; evidence/optimisation.json |
| Actual bill and term total | Pending published charges and shared-resource allocation | evidence/lab5-billing.json |
| Teardown | Independently verified empty: endpoints, computes, schedules, identities, active jobs and LLM accounts; restricted grant deleted | evidence/resource-inventory.json; evidence/cleanup-protection-proof.json; evidence/console-verification.json; evidence/azure-resources-after.jpg |
| LLM golden set | 14 cases; clarified capped live candidate passed 14/14 | evals/golden/maintenance.jsonl; evidence/live-v2-capped-eval.json |
| Regression and guardrail | Actual faulty live prompt caused seven regressions; output validation demonstrated | evidence/live-gate-command.json; evidence/live-guardrail-proof.json |
| Token accounting | 60 successful calls; provider-reported usage totals 0.3922373697 THB at verified retail rates | evidence/live-v2-token-summary.json; lab5-cost.md |
| Local and mechanical checks | 63 tests pass; full lint passes; instructor grader 10 passed / 0 failed on a fresh clone | evidence/local-validation.json; evidence/mechanical-grading.json |

The mechanical grader checks structure and local behaviour. It does not substitute for the second cloud, the final bill, or provider-console teardown verification. The original price forecast remains unchanged in its pre-run commit; actual billing must be reconciled honestly rather than fitted to the forecast.

The next-day billing and cleanup check is scheduled through the local desktop automation lab-5-next-day-billing-recheck. It makes read-only cloud requests and pauses after its first attempt. Keep this computer awake with Codex running for that local follow-up.
