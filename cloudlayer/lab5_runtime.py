"""Managed pipeline stages: a rejected gate exits before any registry/deployment mutation."""

from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path

import joblib
import yaml
from sklearn.metrics import roc_auc_score

from src import contracts, data
from src.gate import evaluate
from src.workflow import train


def model_version(run_id):
    # Azure ML accepts positive integer versions, not arbitrary job IDs.
    return str(int(hashlib.sha256(run_id.encode()).hexdigest()[:7], 16) + 1)


def client():
    from azure.ai.ml import MLClient
    from azure.identity import ManagedIdentityCredential

    return MLClient(
        ManagedIdentityCredential(client_id=os.environ["AZURE_CLIENT_ID"]),
        os.environ["AZURE_SUBSCRIPTION_ID"],
        os.environ["AZURE_RESOURCE_GROUP"],
        os.environ["AZUREML_WORKSPACE"],
    )


def incumbent_score(ml, source, metrics, bootstrap):
    from azure.core.exceptions import ResourceNotFoundError

    # Query the workspace collection first: Azure can return AuthorizationFailed
    # for a child lookup whose parent endpoint has never existed.
    if not any(ep.name == "itcs355-lab5-staging" for ep in ml.online_endpoints.list()):
        if bootstrap:
            return None
        raise RuntimeError("No deployed incumbent; explicit bootstrap required")
    try:
        deployed = ml.online_deployments.get(endpoint_name="itcs355-lab5-staging", name="blue")
    except ResourceNotFoundError:
        if bootstrap:
            return None
        raise RuntimeError("No deployed incumbent; explicit bootstrap required")
    model_id = deployed.model.id if hasattr(deployed.model, "id") else deployed.model
    model = ml.models.get(
        name=model_id.split("/models/")[1].split("/")[0], version=model_id.rsplit("/", 1)[1]
    )
    destination = Path("/tmp/incumbent")
    ml.models.download(name=model.name, version=model.version, download_path=str(destination))
    files = list(destination.rglob("model.joblib"))
    if len(files) != 1:
        raise RuntimeError("Incumbent artifact is missing or ambiguous")
    incumbent = joblib.load(files[0])
    _, validation, _ = data.split(data.load_raw(source), seed=metrics["seed"])
    return float(
        roc_auc_score(
            validation[data.TARGET], incumbent.predict_proba(validation[data.FEATURES])[:, 1]
        )
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True)
    ap.add_argument("--source", type=Path)
    ap.add_argument("--input", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--bootstrap", action="store_true")
    ap.add_argument(
        "--incumbent", type=float, help="Fault-injection only; omit for the deployed incumbent"
    )
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.input:
        shutil.copytree(args.input, args.out, dirs_exist_ok=True)
    source = args.out / "sensors.csv"
    if args.stage == "ingest":
        shutil.copyfile(args.source, source)
    elif args.stage == "validate":
        contracts.validate(data.load_raw(source))
    elif args.stage == "train":
        train(source, args.out)
    elif args.stage == "evaluate":
        metrics = json.loads((args.out / "metrics.json").read_text())
        incumbent = args.incumbent
        if incumbent is None:
            incumbent = incumbent_score(client(), source, metrics, args.bootstrap)
        decision = evaluate(metrics["val_roc_auc"], incumbent, bootstrap=args.bootstrap)
        (args.out / "gate.json").write_text(json.dumps(decision.as_dict(), indent=2))
        if not decision.passed:
            raise SystemExit("GATE REJECTED: " + decision.reason)
    elif args.stage == "register":
        gate = json.loads((args.out / "gate.json").read_text())
        if gate.get("passed") is not True:
            raise RuntimeError("Refusing registration without a passing decision")
        from azure.ai.ml.entities import Model

        metrics = json.loads((args.out / "metrics.json").read_text())
        artifact = args.out / "registered_artifact"
        artifact.mkdir(exist_ok=True)
        shutil.copyfile(args.out / "model.joblib", artifact / "model.joblib")
        version = model_version(os.environ.get("AZUREML_RUN_ID", "manual"))
        asset = client().models.create_or_update(
            Model(
                name="itcs355-lab5",
                version=version,
                path=str(artifact),
                type="custom_model",
                tags={"course": "itcs355", "lab": "5"},
                properties={k: str(v) for k, v in metrics.items()},
            )
        )
        (args.out / "registered.json").write_text(
            json.dumps({"id": asset.id, "version": asset.version})
        )
    elif args.stage == "deploy_staging":
        from io import StringIO
        from azure.ai.ml import load_online_endpoint, load_online_deployment
        from azure.core.exceptions import ResourceNotFoundError

        ml = client()
        registered = json.loads((args.out / "registered.json").read_text())
        tags = {"course": "itcs355", "lab": "5"}
        try:
            ml.online_endpoints.get("itcs355-lab5-staging")
        except ResourceNotFoundError:
            endpoint = dict(
                name="itcs355-lab5-staging",
                auth_mode="key",
                tags=tags,
                identity={
                    "type": "user_assigned",
                    "user_assigned_identities": [
                        {"resource_id": os.environ["SERVING_IDENTITY_ID"]}
                    ],
                },
            )
            ml.online_endpoints.begin_create_or_update(
                load_online_endpoint(source=StringIO(yaml.safe_dump(endpoint)))
            ).result()
        routes = {
            name: {"port": 8080, "path": path}
            for name, path in [
                ("liveness_route", "/health"),
                ("readiness_route", "/ready"),
                ("scoring_route", "/predict"),
            ]
        }
        spec = dict(
            name="blue",
            endpoint_name="itcs355-lab5-staging",
            model=registered["id"],
            environment={"image": os.environ["SERVING_IMAGE"], "inference_config": routes},
            instance_type="Standard_DS2_v2",
            instance_count=1,
            tags=tags,
            environment_variables={"MODEL_VERSION": registered["version"]},
        )
        ml.online_deployments.begin_create_or_update(
            load_online_deployment(source=StringIO(yaml.safe_dump(spec)))
        ).result()
        ep = ml.online_endpoints.get("itcs355-lab5-staging")
        ep.traffic = {"blue": 100}
        ml.online_endpoints.begin_create_or_update(ep).result()
        payload = args.out / "request.json"
        payload.write_text(
            json.dumps(
                dict(
                    temp_c=78.4,
                    vibration_mm_s=3.1,
                    pressure_kpa=315.2,
                    hours_since_service=4200,
                    load_pct=68,
                    ambient_humidity=55,
                )
            )
        )
        response = json.loads(
            ml.online_endpoints.invoke(endpoint_name=ep.name, request_file=str(payload))
        )
        if (
            response.get("model_version") != registered["version"]
            or not 0 <= response["probability"] <= 1
        ):
            raise RuntimeError("Staging response failed model identity/probability check")
        (args.out / "deployment.json").write_text(json.dumps(response, indent=2))
    else:
        raise ValueError("Unknown stage")
    print("COMPLETED: " + args.stage)


if __name__ == "__main__":
    main()
