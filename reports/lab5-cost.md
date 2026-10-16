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

## 7. Measured LLM usage and budget defence

The initial Southeast Asia account creation was denied by the subscription's allowed-region policy. The user approved Korea Central as the replacement. The temporary OpenAI S0 account deployed gpt-5-mini 2025-08-07 with GlobalStandard. The original provider receipts, model/request IDs, prompt hashes, completion caps and cache counters are retained in evidence/live*.jsonl. Four safety/insufficient-input cases in each 14-case run were resolved locally; the other ten made provider calls. Local refusals have no invented provider usage.

Current Microsoft retail API prices, verified 2026-10-16 for Korea Central, are USD0.25 fresh input, USD0.025 cached input and USD2 output per million tokens. At the captured 33.5403283369 THB/USD FX these are 8.3850820842, 0.8385082084 and 67.0806566738 THB per million respectively. Exact SKU/meter IDs and effective dates are in evidence/llm-price-query.json. Hidden reasoning tokens are included in provider completion usage.

| Observed run | Provider input / output / cached tokens | THB/1,000 provider calls | Golden result |
|---|---|---:|---|
| Initial prompt, cap 1,000 | 1,656 / 900 / 0 over ten calls | 7.4258 | 10/14 |
| Clarified prompt, cap 1,000 | 2,176 / 683 / 0 over ten calls | 6.4062 | 13/14 |
| Same clarified prompt, cap 500 | 2,176 / 731 / 0 over ten calls | 6.7282 | 14/14, gate passed |

Working for the capped run: ((2,176 × 0.25 + 731 × 2) / 1,000,000) × 33.5403283369 / 10 × 1,000 = 6.7282 THB per 1,000 provider calls. Including the four free local-policy cases, the observed 14-case application mix costs 0.0672818986 / 14 × 1,000 = 4.8058 THB per 1,000 application requests. That mix is specific to this golden set, not a production traffic forecast.

**Output cap result:** 6.4062 − 6.7282 = **−0.3220 THB/1,000 provider calls**, an observed 5.03% increase. Neither cap was reached: this small sequential comparison does not establish causal savings from lowering the cap. The 500-token run passed every case; retain the lower ceiling to bound worst-case completion exposure, but do not describe it as a measured cost reduction. The first capped attempt failed 2 cases and was rejected; its receipts remain in the evidence.

**Prompt-cache result:** measured cached tokens were zero and request hit rate was 0/10 = 0%. GPT-5 mini uses automatic caching with no extra cache-write surcharge. Break-even = 0 / (0 + 8.3850820842 − 0.8385082084) = **0%**. With no observed hits, there was no observed caching benefit. The short prompts were below the documented 1,024-token eligibility threshold; padding them merely to claim a hit would add cost. Model-specific source: https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/prompt-caching .

Across all six live sets there were 60 successful provider calls and 64 request attempts (four rate-limited retries). Provider-receipt cost at current retail rates totals **0.3922373697 THB**, within the approved 10 THB LLM allowance. This is token accounting, not the final Azure invoice. The final clarified baseline passed 13/14; the deliberately faulty prompt passed 6/14 and the gate named seven regressions. The capped clarified candidate passed 14/14. The small sample demonstrates the controls, not universal model reliability.

Budget defence: the selected capped assistant costs about 6.73 THB per 1,000 model calls, or 4.81 THB per 1,000 requests for this measured mix with local refusals. Clearer instructions and output validation caught real model failures. Reducing the cap did not save money in the measured sample, so we claim no such saving. We retained the cap to limit exposure and used actual scale-to-zero for the infrastructure optimisation. Every fallback still requires an engineer to confirm maintenance; the assistant never operates machinery. Final shared-infrastructure billing and the 800 THB term total still need the delayed bill.
