"""Azure operations for this lab, scoped to tagged resources and an explicit workspace."""

from __future__ import annotations
import argparse
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/evidence"
SUB = "6638a4ea-96da-4326-969a-2e40305cfc83"
RG = WS = "itcs355-6688218"
COMPUTE = "lab5-cpu"
TAGS = {"course": "itcs355", "lab": "5"}


def az(*args):
    result = subprocess.run(["az", *args], check=True, capture_output=True, text=True)
    return json.loads(result.stdout) if result.stdout.strip() else None


def save(name, data):
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / name).write_text(json.dumps(data, indent=2, default=str) + "\n")


def ml_client():
    from azure.ai.ml import MLClient
    from azure.identity import AzureCliCredential

    return MLClient(AzureCliCredential(), SUB, RG, WS)


def settings():
    return json.loads((ROOT / "reports/cloud-settings.json").read_text())


def assign(principal, role, scope):
    return az(
        "role",
        "assignment",
        "create",
        "--assignee-object-id",
        principal,
        "--assignee-principal-type",
        "ServicePrincipal",
        "--role",
        role,
        "--scope",
        scope,
        "-o",
        "json",
    )


def provision():
    from azure.ai.ml.entities import (
        AmlCompute,
        IdentityConfiguration,
        ManagedIdentityConfiguration,
        Environment,
    )

    workspace = az("ml", "workspace", "show", "-n", WS, "-g", RG, "-o", "json")
    storage_id = workspace["storage_account"]
    registry_id = workspace["container_registry"]
    registry = registry_id.rsplit("/", 1)[1]
    store = az(
        "ml", "datastore", "show", "-n", "workspaceblobstore", "-g", RG, "-w", WS, "-o", "json"
    )
    container_scope = storage_id + "/blobServices/default/containers/" + store["container_name"]
    identities = {}
    assignments = []
    for purpose in ("training", "serving", "ci"):
        identity = az(
            "identity",
            "create",
            "-n",
            "lab5-" + purpose,
            "-g",
            RG,
            "-l",
            "eastasia",
            "--tags",
            "course=itcs355",
            "lab=5",
            "-o",
            "json",
        )
        identities[purpose] = identity
    for purpose, role, scope in [
        ("training", "Reader", workspace["id"]),
        ("training", "Storage Blob Data Contributor", container_scope),
        ("training", "AcrPull", registry_id),
        ("serving", "Storage Blob Data Reader", container_scope),
        ("serving", "AcrPull", registry_id),
        ("ci", "AzureML Data Scientist", workspace["id"]),
        ("ci", "Storage Blob Data Contributor", container_scope),
        ("ci", "AcrPush", registry_id),
        ("ci", "Managed Identity Operator", identities["serving"]["id"]),
    ]:
        assignments.append(assign(identities[purpose]["principalId"], role, scope))
    if workspace.get("application_insights"):
        assignments.append(
            assign(
                identities["serving"]["principalId"],
                "Monitoring Metrics Publisher",
                workspace["application_insights"],
            )
        )
    save("identity-assignments.json", dict(identities=identities, assignments=assignments))
    ml = ml_client()
    compute = AmlCompute(
        name=COMPUTE,
        size="Standard_DS2_v2",
        min_instances=0,
        max_instances=1,
        idle_time_before_scale_down=60,
        tags=TAGS,
        identity=IdentityConfiguration(
            type="user_assigned",
            user_assigned_identities=[
                ManagedIdentityConfiguration(resource_id=identities[p]["id"])
                for p in ("training", "ci")
            ],
        ),
    )
    ml.compute.begin_create_or_update(compute).result()
    image = registry + ".azurecr.io/itcs355-lab5:c3b7231"
    env = ml.environments.create_or_update(
        Environment(name="itcs355-lab5", version="c3b7231", image=image, tags=TAGS)
    )
    data = dict(
        environment=env.id,
        compute=COMPUTE,
        training_client_id=identities["training"]["clientId"],
        ci_client_id=identities["ci"]["clientId"],
        runtime_env={
            "AZURE_SUBSCRIPTION_ID": SUB,
            "AZURE_RESOURCE_GROUP": RG,
            "AZUREML_WORKSPACE": WS,
            "SERVING_IDENTITY_ID": identities["serving"]["id"],
            "SERVING_IMAGE": image,
        },
        storage_account=store["account_name"],
        container=store["container_name"],
        container_scope=container_scope,
        identities=identities,
    )
    (ROOT / "reports/cloud-settings.json").write_text(json.dumps(data, indent=2))
    save(
        "provisioning.json",
        dict(compute=COMPUTE, environment=env.id, at=datetime.now(timezone.utc).isoformat()),
    )
    return data


def submit(reject=False, bootstrap=False):
    from cloudlayer.pipelines import compile_azure

    import hashlib
    from azure.ai.ml.entities import Data

    ml = ml_client()
    source = ROOT / "data/raw/sensors.csv"
    from azure.core.exceptions import ResourceNotFoundError

    version = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
    try:
        asset = ml.data.get(name="itcs355-lab5-sensors", version=version)
    except ResourceNotFoundError:
        asset = ml.data.create_or_update(
            Data(
                name="itcs355-lab5-sensors",
                version=version,
                type="uri_file",
                path=str(source),
                tags=TAGS,
            )
        )
    cfg = settings()
    cfg["source_asset"] = asset.id
    cfg["runtime_env"]["CODE_VERSION"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    (ROOT / "reports/cloud-settings.json").write_text(json.dumps(cfg, indent=2))
    job = compile_azure(
        cfg, bootstrap=bootstrap and not reject, forced_incumbent=0.99 if reject else None
    )
    result = ml_client().jobs.create_or_update(job)
    save(
        "managed-rejected-run.json" if reject else "managed-run.json",
        dict(name=result.name, studio_url=result.studio_url, status=result.status),
    )
    print(result.name, flush=True)
    return result.name


def status(name):
    ml = ml_client()
    run = ml.jobs.get(name)
    result = dict(
        name=name,
        status=run.status,
        studio_url=run.studio_url,
        children=[
            dict(name=j.name, status=j.status, display_name=j.display_name)
            for j in ml.jobs.list(parent_job_name=name)
        ],
    )
    save("status-" + name + ".json", result)
    print(json.dumps(result, indent=2))
    return result


def schedule(name):
    from azure.ai.ml.entities import JobSchedule, CronTrigger
    from cloudlayer.pipelines import compile_azure

    result = (
        ml_client()
        .schedules.begin_create_or_update(
            JobSchedule(
                name="lab5-weekly",
                trigger=CronTrigger(expression="0 2 * * 0", time_zone="UTC"),
                create_job=compile_azure(settings(), bootstrap=False),
                tags=TAGS,
            )
        )
        .result()
    )
    save("schedule.json", dict(name=result.name, is_enabled=result.is_enabled))


def inventory():
    ml = ml_client()
    result = {}
    for kind, operations in [
        ("endpoints", ml.online_endpoints),
        ("computes", ml.compute),
        ("schedules", ml.schedules),
    ]:
        result[kind] = [
            dict(name=x.name, tags=x.tags)
            for x in operations.list()
            if (x.tags or {}).get("lab") == "5" and (x.tags or {}).get("course") == "itcs355"
        ]
    result["identities"] = az(
        "identity",
        "list",
        "-g",
        RG,
        "--query",
        "[?tags.lab=='5' && tags.course=='itcs355'].{id:id,name:name}",
        "-o",
        "json",
    )
    result["active_jobs"] = [
        dict(name=j.name, status=j.status)
        for j in ml.jobs.list()
        if all((j.tags or {}).get(k) == v for k, v in TAGS.items())
        and j.status not in {"Completed", "Failed", "Canceled"}
    ]
    result["llm_accounts"] = az(
        "cognitiveservices", "account", "list", "-g", RG, "--query",
        "[?tags.lab=='5' && tags.course=='itcs355'].{id:id,name:name}", "-o", "json"
    )
    save(
        "resource-inventory.json",
        dict(captured_at=datetime.now(timezone.utc).isoformat(), **result),
    )
    return result


def teardown():
    ml = ml_client()
    def owned(item, name):
        return item.name == name and all((item.tags or {}).get(k) == v for k, v in TAGS.items())

    for item in list(ml.schedules.list()):
        if owned(item, "lab5-weekly"):
            ml.schedules.begin_disable(item.name).result()
            ml.schedules.begin_delete(item.name).result()
    for item in list(ml.online_endpoints.list()):
        if owned(item, "itcs355-lab5-staging"):
            ml.online_endpoints.begin_delete(item.name).result()
    for item in list(ml.compute.list()):
        if owned(item, COMPUTE):
            ml.compute.begin_delete(item.name).result()
    # Remove scoped assignments attached to only the recorded Lab 5 identities.
    record = EVIDENCE / "identity-assignments.json"
    if record.exists():
        info = json.loads(record.read_text())
        for assignment in info["assignments"]:
            az("role", "assignment", "delete", "--ids", assignment["id"])
        for identity in info["identities"].values():
            az("identity", "delete", "--ids", identity["id"])
    result = inventory()
    if any(result.values()):
        raise RuntimeError("Lab 5 resources remain after deletion")
    print("Verified no tagged Lab 5 endpoints, compute, schedules or identities remain")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "action",
        choices=["provision", "submit", "reject", "status", "schedule", "inventory", "teardown"],
    )
    ap.add_argument("--name")
    ap.add_argument("--bootstrap", action="store_true")
    args = ap.parse_args()
    if args.action == "provision":
        provision()
    elif args.action in ("submit", "reject"):
        submit(args.action == "reject", bootstrap=args.bootstrap)
    elif args.action == "status":
        status(args.name)
    elif args.action == "schedule":
        schedule(args.name)
    elif args.action == "inventory":
        print(json.dumps(inventory(), indent=2))
    elif args.action == "teardown":
        teardown()


if __name__ == "__main__":
    main()
