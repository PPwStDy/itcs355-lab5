# Lab 5 cost report — evidence in progress

## 1. Estimate before running
39.42 THB, calculated and committed before the managed pipeline in commit c3b7231. The exact price inputs, exchange rate, runtime allowances and contingency are in pre-run-estimate.md and evidence/planning-prices.json. The spending ceiling is 150 THB, subject to the remaining 800 THB course allowance.

## 2. Actual from billing
Not yet final. Azure bills arrive after activity; no empty or unavailable query will be reported as zero actual cost. The pre-run course-tag query returned USD 6.95145721947742, approximately 233.15 THB at the captured ECB rate, before this lab. This is prior term spend, not Lab 5's bill.

## 3. Gap
Pending the Lab 5 bill. The estimate allows one training VM-hour, two serving VM-hours, a 10 THB overhead/LLM allowance and 25% contingency. Shorter active runtime or delayed deletion will move the result in opposite directions. Shared workspace storage and registry spend need explicit allocation rather than relabelling an existing shared resource as Lab 5.

## 4. Component accounting
Training, storage, serving, pipeline, monitoring and LLM will be recorded individually. Azure ML runtime and endpoint resources carry course=itcs355, lab=5. Shared storage/registry costs must be attributed separately with the stated allocation basis. Billing retrieval and classification evidence is required before reporting a total.

## 5. Cost per 1,000 predictions
The scenario calculator covers 5%, 25% and 80% utilisation. The formula is hourly_THB × 1,000 / (3,600 × measured_capacity_RPS × utilisation). No measured cloud throughput is available yet, so no numerical cloud prediction cost is claimed.

## 6. Applied optimisation
Applied and observed: the isolated training cluster changed from min_instances=1 to 0, max_instances=1, with a 60-second idle timer. The actual node list changed from one idle node to zero in 177.33 seconds. At the verified East Asia DS2_v2 price and captured FX, this removes 7.1776 THB/hour of idle VM capacity while no work is scheduled. See evidence/optimisation.json. This is a measured resource reduction priced at retail; invoice savings remain pending. Subsequent work can scale the cluster up again, and the cluster is deleted at final teardown.

## 7. LLM usage and budget defence
East Asia has no synchronous GPT chat quota. After registering Microsoft.CognitiveServices, Southeast Asia exposed GPT-5 mini GlobalStandard quota. The user approved an LLM-only region amendment, but Azure rejected account creation with RequestDisallowedByAzure because Southeast Asia is outside this subscription’s allowed deployment regions. No paid LLM deployment was created. See evidence/llm-capacity-check.json, subscription-region-policy.json and llm-provisioning-blocked.json. Authored baseline/regressed fixtures contain no provider token counts and cannot establish a token bill.

The live recorder and calculator require actual provider usage receipts, a dated exact model/region price source, observed cache counters, and a second measured output-cap run that passes the same golden set. Until a usable LLM endpoint is available, THB/1,000 LLM requests, output-cap savings and measured cache break-even comparison remain unmeasured. Inventing values would fail the lab's stated acceptance criterion.

Budget defence: the classical ML exercise is capped at the approved 150 THB additional spend and uses existing supporting infrastructure, a scale-to-zero training cluster and prompt teardown. We have made no claim that a shorter LLM output is cheaper or equally accurate without measured provider calls and a passing capped evaluation.
