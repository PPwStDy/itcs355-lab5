"""Capture completed managed pipeline outputs and measured endpoint responses."""

from __future__ import annotations
import json
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from cloudlayer.manage import ROOT, ml_client, save
from src.accounting import compute_scenarios


def main():
    record = json.loads((ROOT / "reports/evidence/managed-run.json").read_text())
    name = record["name"]
    ml = ml_client()
    run = ml.jobs.get(name)
    children = list(ml.jobs.list(parent_job_name=name))
    stages = {"ingest", "validate", "train", "evaluate", "register", "deploy_staging"}
    if (
        run.status != "Completed"
        or {x.display_name for x in children} != stages
        or any(x.status != "Completed" for x in children)
    ):
        raise RuntimeError("Full managed pipeline has not completed successfully")
    deploy = next(x for x in children if x.display_name == "deploy_staging")
    outputs = {}
    with tempfile.TemporaryDirectory() as folder:
        ml.jobs.download(deploy.name, download_path=folder, output_name="result")
        for filename in ("metrics.json", "gate.json", "registered.json", "deployment.json"):
            files = list(Path(folder).rglob(filename))
            if len(files) != 1:
                raise RuntimeError("Missing or ambiguous managed output " + filename)
            outputs[filename] = json.loads(files[0].read_text())
    save(
        "managed-success.json",
        dict(
            name=name,
            status=run.status,
            stages=[dict(name=x.display_name, status=x.status, job=x.name) for x in children],
            outputs=outputs,
        ),
    )
    ep = ml.online_endpoints.get("itcs355-lab5-staging")
    key = ml.online_endpoints.get_keys(ep.name).primary_key
    payload = dict(
        temp_c=78.4,
        vibration_mm_s=3.1,
        pressure_kpa=315.2,
        hours_since_service=4200,
        load_pct=68,
        ambient_humidity=55,
    )
    latencies = []
    responses = []
    for index in range(30):
        req = urllib.request.Request(
            ep.scoring_uri,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + key},
        )
        start = time.perf_counter()
        with urllib.request.urlopen(req, timeout=30) as response:
            body = json.load(response)
        if (
            body["model_version"] != outputs["registered.json"]["version"]
            or not 0 <= body["probability"] <= 1
        ):
            raise RuntimeError("Endpoint returned the wrong model or invalid probability")
        if index >= 5:
            latencies.append(time.perf_counter() - start)
            responses.append(body)
    elapsed = sum(latencies)
    rps = len(latencies) / elapsed
    prices = json.loads((ROOT / "reports/evidence/planning-prices.json").read_text())
    hourly = max(x["retailPrice"] for x in prices["prices"]) * prices["exchange"]["usd_thb"]
    result = dict(
        captured_at=datetime.now(timezone.utc).isoformat(),
        samples=len(latencies),
        warmup=5,
        concurrency=1,
        observed_rps=rps,
        latency_p50_ms=median(latencies) * 1000,
        latency_p95_ms=sorted(latencies)[int(0.95 * (len(latencies) - 1))] * 1000,
        model_version=responses[-1]["model_version"],
        response=responses[-1],
        hourly_thb=hourly,
        cost_per_1000_by_utilisation=compute_scenarios(hourly, rps),
        limitation="Sequential client-observed throughput, not a saturation capacity test; scenario costs assume this nominal throughput.",
    )
    save("endpoint-benchmark.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
