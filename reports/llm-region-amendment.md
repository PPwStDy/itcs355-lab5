# LLM-only region amendment — approved; blocked by Azure policy

Keep the managed ML workspace, training cluster and classical endpoint in East Asia. The account has no synchronous GPT chat quota there. After registering Microsoft.CognitiveServices, the actual quota API reports 500 available GlobalStandard capacity units for gpt-5-mini in Southeast Asia; model version 2025-08-07 is generally available there. See evidence/llm-capacity-check.json and llm-southeastasia-model.json.

Proposed isolated resource: lab5-llm-6688218 in the existing itcs355-6688218 resource group, Southeast Asia; OpenAI S0 account, one gpt-5-mini 2025-08-07 GlobalStandard deployment, 10 capacity units. GlobalStandard may process requests globally. Use only synthetic maintenance cases. No provisioned throughput.

Run a baseline, a changed-prompt regression and a capped-output comparison, retaining original provider usage and cache counters. At most 100 calls, at most 1,000 completion tokens per call and a small fixed prompt; stop after 10 THB of token charges. This uses the existing 10 THB LLM/overhead allowance and does not raise the approved 150 THB total ceiling. Microsoft published global rates of USD 0.25 input, 0.025 cached input and 2 output per million tokens: https://devblogs.microsoft.com/foundry/whats-new-in-azure-ai-foundry-august-2025/ . Reconfirm current rate before making calls; public pricing query has not yet returned model meters.

Delete the deployment and this exact account after recording results. Verify its absence in the same final inventory and portal screenshot. No AWS/GCP account creation or subscription upgrade is included.

Approval is needed because the previously approved plan names East Asia, while this amendment adds an LLM resource in Southeast Asia.

User approved the Southeast Asia amendment. Azure rejected account creation with RequestDisallowedByAzure. Quota alone does not establish deployment eligibility. No account or paid model was created. Do not bypass the subscription policy or change regions without authorization.

## Replacement candidate — Korea Central

Korea Central is explicitly included in the subscription's allowed-region policy and has 500K TPM platform capacity and 500K TPM available subscription quota for gpt-5-mini 2025-08-07 GlobalStandard. The capacity skill's read-only check passed. Proposed resource name, group, S0/GlobalStandard settings, 10-unit deployment, synthetic data, 100-call/1,000-completion-token limits, 10 THB LLM ceiling, 150 THB overall ceiling and immediate teardown are unchanged. Only account region changes from the denied Southeast Asia to Korea Central. Await user approval before account creation.
