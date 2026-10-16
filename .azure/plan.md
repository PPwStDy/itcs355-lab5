# Lab 5 Azure deployment plan

Status: Validated — azure-validate checks passed; approved Azure execution may proceed.
Generated: 2026-10-16 (Asia/Bangkok).

## Objective
Complete ITCS355 Lab 5 on the sensor-maintenance service: managed ingest → validate → train → evaluate → conditional register → staging deployment, separate identities, retraining schedule, provider swap, real billing and LLM evaluation with usage accounting.

## Proposed context
- Current signed-in subscription: Azure for Students (6638a4ea-96da-4326-969a-2e40305cfc83).
- Approved primary location: East Asia. The user also approved a temporary Southeast Asia LLM test; that region was denied by subscription policy, so no LLM account was created. Korea Central was approved as the replacement; the temporary LLM account was deployed, exercised and deleted.
- Additional spending ceiling proposed: ฿150, and never exceed the remaining ฿800 term allowance.
- Reuse suitable existing Azure ML workspace, registry and storage only after checking ownership and tags.
- Recipe: Azure CLI, matching the existing labs' Azure ML and CLI conventions.
- Second provider: select AWS or GCP after user identifies an available account.
- Scope: development lab, short-lived endpoint, minimum compute, teardown after verified evidence.

## Resource and capacity inventory
Read-only inventory and the azure-quotas skill verified the following in East Asia:

| Resource/capacity | Current | Proposed addition / use | Total/peak | Limit/source |
|---|---:|---:|---:|---|
| DSv2 dedicated vCPUs | 0 | training 2 + serving 2 | 4 | 6; az quota show/usage show, standardDSv2Family |
| ML training clusters | 1 | 1 isolated lab5-cpu, min=0/max=1 | 2 | 200; az quota list TotalClusters |
| Managed online endpoints | 0 | 1 itcs355-lab5-staging | 1 | 100 default regional endpoint cap; Microsoft ML quota documentation |
| Workspace | 1 existing | reuse | 1 | No new workspace |
| Storage / registry | workspace-managed existing | reuse | no new account/registry | Inspect access and image build permission before use |
| Retraining schedule | no Lab 5 schedule created | 1, weekly UTC | 1 Lab 5 schedule | Disable and remove during teardown |
| Scoped identities | existing cluster has no explicitly assigned identity | training, serving, CI user-assigned identities | 3 Lab 5 identities | Validate Entra and scoped role-assignment permissions before provisioning |

Do not change the existing cpu-cluster. Create tagged Lab 5 resources and remove only resources created for this lab. Identity permissions and platform SKU availability must pass azure-validate before deployment. No GPU or new persistent LLM capacity is proposed.

Official endpoint-limit reference: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-quotas?view=azureml-api-2

The current calculated forecast is approximately 39.42 THB (see reports/pre-run-estimate.md), with an additional spending ceiling of 150 THB. Managed runs and current completion/failure evidence are retained under reports/evidence.

## Approval boundary
Offline evaluation, cost arithmetic, tests, documentation and provider-neutral pipeline logic proceed independently. Azure-specific infrastructure generation/deployment waits for the approved, quota-validated plan. The azure-prepare skill requires: “Get approval — Present plan to user before execution”.

## Local deliverables
- Actual rejection path prevents registration and deployment.
- Separate validation and held-out evaluation data; lineage and content hashes.
- Ten or more maintenance golden cases, measured guardrail failure, a baseline and per-case regression gate.
- Honest distinction between offline fixtures and provider-recorded token usage.
- Cost evidence import with fail-closed missing billing or token records.
- Read-only teardown verification; deletion is a separate operation.

## Cloud execution checklist
- [x] Confirm Azure subscription, primary region and budget.
- [ ] Second-provider account still unavailable.
- [x] Read-only workspace/cluster/endpoint inventory and DSv2 quota validation.
- [x] User approved concrete cloud plan, spending ceiling and teardown.
- [x] Commit pre-run estimate before submitting any managed run (c3b7231).
- [x] Implement/validate provider pipeline, scoped identities and schedule.
- [x] Run a deliberately failing managed gate; registration and deployment never started.
- [ ] Complete the accepted six-stage managed run.
- [x] Demonstrate revoked permission (actual 403) and restore only that permission.
- [x] Confirm restored Reader access from a managed job after Azure propagation (funny_cake_2b2kbzz208).
- [ ] Demonstrate real second-provider upload/download/invoke.
- [x] Record live LLM usage, capped run, cache observations and current price sources; all LLM calls total 0.3922373697 THB at retail.
- [ ] Capture billing and console evidence; remove only Lab 5 resources.
- [ ] Verify empty lists and delayed billing after 24 hours.

Actual cloud execution is in progress. One idle node was observed scaling to zero in 177.33 seconds; this removes 7.1776 THB/hour of idle retail capacity. Invoice savings and full billing remain pending.

## 7. Validation proof (azure-validate)

Validation timestamp: 2026-10-16T08:03:31.893371+00:00.

| Check | Actual command/result |
|---|---|
| Subscription/authentication | az account show: Azure for Students, expected subscription Enabled |
| Regional quota | az quota show / usage show: DSv2 6 limit, 0 used; planned 4 cores |
| Python tests | .venv/bin/python -m pytest -q tests cloudlayer/tests: 50 passed |
| Lint | ruff check application, scripts, tests and new cloud runtime: passed |
| Portability | scripts/portability_audit.py: zero hits |
| Pipeline schema | compile_azure(...)._validate(): Succeeded; six-stage YAML generated |
| Infrastructure syntax | az bicep build --file infra/main.bicep: passed |
| ARM validation | az deployment group validate: Succeeded, no error |
| Preview | az deployment group what-if: three new Lab 5 identities only; existing resources Ignore |
| Container build | Azure ACR build ck1: Succeeded, image digest sha256:c8b4e4a1d7843c69e417e55c67cae352446551b1e22961abd31a310c36595be2 |

Validated by the azure-validate workflow. Azure CLI/SDK service operations are used; no new workspace, storage account or registry is provisioned. The user approved this subscription, East Asia, spending limits and teardown.

Final local verification after the LLM transport and validation changes: 59 tests passed; lint and portability audit passed. Live golden gate: faulty prompt exited 1 with seven regressions, capped candidate exited 0 with 14/14.
