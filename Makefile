SHELL := /bin/bash
PYTHON ?= python
.PHONY: data test lint portability-audit pipeline pipeline-submit pipeline-local pipeline-reject pipeline-reject-local llm-eval llm-gate guardrail cost-report swap-check teardown teardown-verify billing

data:
	$(PYTHON) scripts/make_dataset.py

test: data
	$(PYTHON) -m pytest -q tests cloudlayer/tests

lint:
	$(PYTHON) -m ruff check src/ service/ monitoring/ scripts/ tests/

portability-audit:
	$(PYTHON) scripts/portability_audit.py

pipeline:
	$(PYTHON) -c "from cloudlayer.pipelines import compile_for; compile_for('azure').dump('reports/managed-pipeline.yml')"

pipeline-submit:
	$(PYTHON) -m cloudlayer.manage submit

pipeline-bootstrap:
	$(PYTHON) -m cloudlayer.manage submit --bootstrap

pipeline-local: data
	$(PYTHON) scripts/run_pipeline.py --bootstrap

pipeline-reject:
	$(PYTHON) -m cloudlayer.manage reject

pipeline-reject-local: data
	$(PYTHON) scripts/run_pipeline.py --incumbent 0.99 --out reports/rejected-pipeline

llm-eval:
	$(PYTHON) scripts/llm_eval.py

llm-gate: llm-eval
	$(PYTHON) scripts/llm_eval.py --responses evals/fixtures/maintenance-regressed.jsonl --baseline reports/evidence/llm-baseline.json --out reports/evidence/llm-regressed.json

guardrail:
	$(PYTHON) scripts/guardrail_demo.py

cost-report:
	$(PYTHON) scripts/cost_report.py --evidence $(EVIDENCE)

swap-check:
	$(PYTHON) scripts/portability_swap_check.py --second-provider $(SECOND_PROVIDER) --blob-uri $(SECOND_BLOB_URI) --region $(SECOND_REGION) --endpoint $(SECOND_ENDPOINT)

teardown:
	$(PYTHON) -m cloudlayer.manage teardown
	$(PYTHON) scripts/teardown_verify.py

teardown-verify:
	$(PYTHON) scripts/teardown_verify.py

billing:
	$(PYTHON) -m cloudlayer.billing
