# ITCS355 Lab 5 — Managed MLOps, Portability and LLM Operations

This is a separate Lab5 folder and Git repository. It builds on the sensor-maintenance system from Lab 4; it does not modify the Lab 4 checkout. The [handout](course/labs/lab-05-cloud-mlops-and-cost.md) defines the submission criteria.

The primary provider is Azure in East Asia. Managed run links and captured results live in [reports/evidence](reports/evidence/README.md). Offline simulation, authored LLM fixtures and SDK transport tests are labelled explicitly; they do not prove a cloud run, a second cloud account or provider token usage.

## Reproduce local checks

```sh
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-cloud.txt
make data
make lint
make portability-audit
make test
make pipeline-local
make pipeline-reject-local   # expected nonzero exit; no register/deploy calls
make llm-eval
make llm-gate                # expected nonzero exit; three named regressions
make guardrail
```

The local pipeline's registry and deployment records are simulations. Source data has 6,000 readings from 240 machines; machine groups never cross train/validation/test boundaries. Required data is generated explicitly; missing data fails rather than silently skipping required tests.

## Task 1 — Managed pipeline and real gate

`pipeline/pipeline.yaml` is the provider-neutral contract. `cloudlayer/pipelines.py` compiles six actual Azure ML command jobs: ingest → validate → train → evaluate → register → deploy_staging. Each output binds to the next job's input; step failures abort the pipeline. Registration also independently requires a true gate decision. Merely writing `condition:` in a neutral YAML would not enforce anything.

The pipeline uses a versioned sensor data asset, an immutable uploaded source snapshot, a custom image built by ACR, a dedicated `lab5-cpu` cluster, and a separate identity for promotion. It registers model, data and validation fingerprints, the seed and evaluation metrics. The current source additionally records its code version and supports atomic warm-start checkpoints every 50 trees; resuming with a different data hash or seed fails closed.

The promotion policy requires validation ROC AUC ≥0.75 and an improvement ≥0.01 over the deployed incumbent. The first run requires explicit bootstrap. Missing incumbent access or a nonfinite score fails. The 0.01 margin is a conservative policy to avoid promoting tiny changes on this small synthetic dataset; it is not a statistically calibrated confidence interval. Before operational use, compare seeds or a paired uncertainty estimate on the same machine groups. Test ROC AUC is reported separately and never drives repeated promotion decisions.

For subsequent runs, evaluation reads the endpoint traffic map and downloads the model attached to the deployment receiving 100% of automatic traffic, then scores it on the candidate's current validation window. Zero-traffic preflight deployments are not serving incumbents; missing automatic traffic still requires explicit bootstrap. Mixed traffic is rejected until an explicit comparison policy is configured. It does not compare stale scores from different datasets. The forced 0.99 incumbent used in the negative exercise is explicitly fault injection, not a real production metric.

```sh
make pipeline               # compile native managed DAG from prepared cloud settings
make pipeline-bootstrap     # explicit first registration only
make pipeline-submit        # compare against the deployed incumbent
make pipeline-reject        # submit deliberately rejecting managed run
python -m cloudlayer.serving_preflight  # optional gated-model test with automatic traffic held at zero
```

`reports/cloud-settings.json` is generated during provisioning and ignored by Git; it contains resource references, never account keys. The approved cloud setup and validation proof are in [.azure/plan.md](.azure/plan.md). The pre-run estimate was committed as `c3b7231` before the first managed run. The runtime image build is recorded in `reports/evidence/container-build.json`; managed jobs also upload the source separately as an immutable code asset.

## Task 2 — Least privilege and a real permission failure

The [identity report](reports/lab5-identities.md) lists training, serving and CI permissions and their exact resource/container scopes. Actual role grants are retained in evidence. The interactive developer identity bootstraps infrastructure; it is not the training or serving runtime identity.

The permission exercise removes only the Lab 5 training identity's workspace Reader grant, then runs a managed probe that attempts to list endpoints using that identity. The expected HTTP 403 proves that blob access alone does not grant control-plane access to the incumbent. A `finally` block restores only the removed grant and updates the teardown journal.

```sh
python -m cloudlayer.permission_exercise
```

Do not treat the role table as proof that this drill ran; inspect `permission-exercise.json` and the captured job log.

## Task 3 — Retraining strategy

| Strategy | When appropriate for this fleet | Failure mode |
|---|---|---|
| Fixed weekly schedule, Sunday 02:00 UTC / 09:00 Bangkok | Predictable maintenance review after accumulating validated, newly labelled machine readings | Wasteful if no new labelled data; calendar time does not establish model degradation. |
| Data volume threshold | At least 1,000 newly labelled readings across 40 distinct machines, after a contract/label audit | A single faulty gateway can flood the threshold; repeated readings from a few machines do not add equivalent evidence. |
| Drift-triggered | Persisting PSI shift plus engineering confirmation that it reflects legitimate process changes, then enough labels for evaluation | A calibration offset is corrupted measurement input. Retraining on it can damage a working model while leaving the producer fault unfixed. |

Chosen policy: weekly review and gated execution with validated data, rather than automatic promotion on drift. The registered demonstration dataset is fixed and is not new production data. An unchanged-data retrain should normally lose to the incumbent or fail the improvement margin. In a real system, ingest would resolve a versioned, newly labelled snapshot before running. The created weekly schedule is captured as configuration evidence and removed at teardown; no future schedule is left running just for a lab demonstration.

## Task 4 — Portability

The audit reports no provider strings or SDK imports in the portable application layers. Only three AWS operations are implemented: upload, download and invoke. The probe uses the URI actually returned by upload, verifies downloaded bytes and validates the prediction/version contract, with separate secondary-provider configuration.

```sh
make swap-check SECOND_PROVIDER=aws SECOND_REGION=REGION \
  SECOND_BLOB_URI=s3://YOUR_BUCKET/PREFIX SECOND_ENDPOINT=YOUR_ENDPOINT
```

No local AWS or GCP credential configuration was found. Transport unit tests prove adapter logic; the real second-provider demonstration remains pending until an account/bucket/endpoint is available. An Azure-only run cannot satisfy a two-provider criterion. The [half-page verdict](reports/lab5-portability.md) explains the hardest method, a real abstraction leak, the estimated migration effort and why only the small seam is worth retaining.

## Task 5 — Bill and optimisation

The [cost report](reports/lab5-cost.md) distinguishes the committed forecast, actual billing, shared-resource allocation, utilisation scenarios and measured optimisation evidence. Exact East Asia VM retail pricing and a dated ECB USD/THB reference are retained. The approved forecast is 39.42 THB; the additional spending ceiling is 150 THB, within the remaining 800 THB course allowance.

`cost_report.py` requires classified, scoped billing rows, dated price/FX evidence, measured throughput and before/after optimisation evidence. Missing billing is an error, not zero spend. The report must be refreshed when delayed Azure billing is available; an immediate post-run empty bill is not final evidence.

## Task 6 — Teardown

```sh
make teardown
make teardown-verify         # read-only; checks without deleting
```

Only the recorded Lab 5 resources and their scoped role grants are removed. Shared registry, workspace, storage and the pre-existing `cpu-cluster` remain in place. Verification lists endpoints, computes, schedules and identities; it must return empty for Lab 5. Completed experiment history and small versioned artifacts may remain for reproducibility, with shared storage allocation disclosed in the bill. Recheck the console and delayed billing after 24 hours. The provider-console screenshot and final inventory are retained under reports/evidence when cleanup completes.

## Tasks 7–8 — Golden set and guardrail

The new maintenance set has 14 independently specified expected decisions, including grounding, safety refusal, injection, insufficient input and threshold boundaries. The authored baseline passes 14/14; the degraded fixture passes 11/14 and the per-case gate names injection, invented vibration and unsafe interlock advice. Missing cases, duplicate response IDs, changes to the golden set and any previously passing case that now fails are rejected.

Operator notes never enter the trusted instruction input. The application validates output schema, exact grounded evidence and the risk/safety decision policy. The demonstration replays an authored unsafe response, records the violation, and emits a deterministic safe fallback; it makes no tool or machinery call. This is control testing, not a claim about a live model's quality.

The live recorder accepts a configured HTTPS chat-completion endpoint and writes raw provider usage, model/request IDs, prompt hashes and output-cap settings. It evaluates raw responses before accepting a change, and retains controlled output separately. Built-in policy refusals are explicitly marked as local, without invented usage.

```sh
python scripts/record_llm.py --max-output-tokens 1000 --out reports/evidence/new-live-baseline.jsonl
python scripts/llm_eval.py --responses reports/evidence/new-live-baseline.jsonl --out reports/evidence/new-live-baseline-eval.json
python scripts/record_llm.py --max-output-tokens 500 --out reports/evidence/new-live-capped.jsonl
python scripts/llm_eval.py --responses reports/evidence/new-live-capped.jsonl \
  --baseline reports/evidence/new-live-baseline-eval.json --out reports/evidence/new-live-capped-eval.json
```

Set `LLM_CHAT_URL`, `LLM_API_KEY`, optionally `LLM_MODEL` and `LLM_AUTH_HEADER` outside Git. For GPT-5 mini set `LLM_REASONING_EFFORT=minimal`; the transport then uses its supported completion-token cap and omits temperature. The initial Southeast Asia alternative was blocked by policy. After user approval, the live exercise ran on GPT-5 mini in Korea Central. Actual receipts show the initial prompt at 10/14, clarified baseline at 13/14, faulty prompt at 6/14 with seven regressions, and the capped clarified candidate at 14/14. `live-gate-command.json` records the real receipt-based gate exiting 1 for the faulty prompt and 0 for the capped candidate. The temporary LLM account is deleted after these runs.

## Task 9 — Token accounting

Token counts must come from provider `prompt_tokens`, `completion_tokens` and cache counters. Normalised values must match the preserved raw receipt. The calculator rejects authored fixtures, missing receipts, mismatches and absent cache telemetry. Prices are supplied for the exact model/region with a dated source; generic “small/medium/large” tutorial prices are not used for this report.

Working per request: (fresh input × input rate + output × output rate + cached reads × cache-read rate + cache writes × cache-write rate) / 1,000,000. Average measured requests ×1,000 gives THB per 1,000 calls. A configured output cap is not a measured saving: compare actual before/after receipts and require the capped eval to pass. Cache break-even is write surcharge / (write surcharge + saving per hit), or not applicable when a hit cannot save money. Azure-style automatic caches with no write surcharge have a zero break-even threshold when reads are cheaper; never impose another provider's cache-write premium.

The live receipts total 0.3922373697 THB at the verified retail rates. The capped candidate costs 6.7282 THB per 1,000 provider calls and recorded a 0% cache hit rate. Lowering the cap did not reduce observed usage; the cost report shows the negative saving and sampling limitation. Invoice reconciliation remains pending.

Replay the actual faulty live response through the guardrail without making a cloud call:

```sh
python scripts/replay_live_guardrail.py
```

This demonstrates a faulty-prompt decision caught by output validation. Operator notes were excluded from provider input, so it is not presented as a successful injected-note attack.
