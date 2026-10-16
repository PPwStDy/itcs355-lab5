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
Planned: the isolated training cluster has min_instances=0, max_instances=1 and a 60-second idle scale-down timer; the staging endpoint will be deleted after the exercise. Actual before/after measurements are required before claiming financial savings. A changed setting alone is not evidence of an optimisation's measured benefit.

## 7. LLM usage and budget defence
The student subscription exposes no pay-as-you-go Azure OpenAI capacity in East Asia; its available model catalogue entries were provisioned-only and the available OpenAI usage query returned an empty set. No provisioned LLM capacity was created. The authored baseline/regressed fixtures contain no provider token counts and cannot establish a token bill.

The live recorder and calculator require actual provider usage receipts, a dated exact model/region price source, observed cache counters, and a second measured output-cap run that passes the same golden set. Until a usable LLM endpoint is available, THB/1,000 LLM requests, output-cap savings and measured cache break-even comparison remain unmeasured. Inventing values would fail the lab's stated acceptance criterion.

Budget defence: the classical ML exercise is capped at the approved 150 THB additional spend and uses existing supporting infrastructure, a scale-to-zero training cluster and prompt teardown. We have made no claim that a shorter LLM output is cheaper or equally accurate without measured provider calls and a passing capped evaluation.
