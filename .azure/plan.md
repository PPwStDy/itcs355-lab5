# Lab 5 Azure deployment plan

Status: Approved — user approved Azure execution and teardown on 2026-10-16.
Generated: 2026-10-16 (Asia/Bangkok).

## Objective
Complete ITCS355 Lab 5 on the sensor-maintenance service: managed ingest → validate → train → evaluate → conditional register → staging deployment, separate identities, retraining schedule, provider swap, real billing and LLM evaluation with usage accounting.

## Proposed context
- Current signed-in subscription: Azure for Students (6638a4ea-96da-4326-969a-2e40305cfc83).
- Proposed location: East Asia; confirm before cloud generation or deployment.
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

The current calculated forecast is approximately 39.42 THB (see reports/pre-run-estimate.md), with an additional spending ceiling of 150 THB. No managed job has been submitted.

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
- [ ] Confirm subscription, region, budget and second provider.
- [x] Read-only workspace/cluster/endpoint inventory and DSv2 quota validation.
- [x] User approved concrete cloud plan, spending ceiling and teardown.
- [ ] Commit pre-run estimate before submitting any managed run.
- [ ] Implement/validate provider pipeline, scoped identities and schedule.
- [ ] Run pipeline including a deliberately failing gate.
- [ ] Demonstrate revoked permission and restore only that permission.
- [ ] Demonstrate real second-provider upload/download/invoke.
- [ ] Record live LLM usage, capped run, cache observations and current price sources.
- [ ] Capture billing and console evidence; remove only Lab 5 resources.
- [ ] Verify empty lists and delayed billing after 24 hours.

No cloud deployment or spending is claimed by this file.
