"""Remove only the lab-created workspace Reader grant, test it, then restore in finally."""

import json
from azure.ai.ml import command
from azure.ai.ml.entities import ManagedIdentityConfiguration
from cloudlayer.manage import ROOT, settings, ml_client, az, assign, save


def main():
    cfg = settings()
    before = json.loads((ROOT / "reports/evidence/identity-assignments.json").read_text())
    principal = cfg["identities"]["training"]["principalId"]
    matches = [
        a
        for a in before["assignments"]
        if a["principalId"] == principal
        and a["roleDefinitionId"].endswith("acdd72a7-3385-48ef-bd42-f606fba81ae7")
    ]
    if len(matches) != 1:
        raise RuntimeError("Cannot identify the exact lab-created workspace Reader grant")
    assignment = matches[0]
    az("role", "assignment", "delete", "--ids", assignment["id"])
    try:
        env = dict(cfg["runtime_env"], AZURE_CLIENT_ID=cfg["training_client_id"])
        job = command(
            code=str(ROOT),
            environment=cfg["environment"],
            compute=cfg["compute"],
            identity=ManagedIdentityConfiguration(client_id=cfg["training_client_id"]),
            environment_variables=env,
            command="python -m cloudlayer.permission_probe",
            experiment_name="itcs355-lab5",
            tags={"course": "itcs355", "lab": "5"},
            display_name="lab5-permission-removal",
        )
        result = ml_client().jobs.create_or_update(job)
        save(
            "permission-exercise.json",
            dict(
                job=result.name,
                removed_assignment_id=assignment["id"],
                expected_status=403,
                restored=False,
            ),
        )
        ml_client().jobs.stream(result.name)
        finished = ml_client().jobs.get(result.name)
        if finished.status != "Completed":
            raise RuntimeError("Permission probe did not confirm the expected denied boundary")
        ml_client().jobs.download(
            result.name, download_path=str(ROOT / "reports/evidence/permission-logs")
        )
    finally:
        restored = assign(principal, "Reader", assignment["scope"])
        # Keep the teardown journal in sync with the replacement grant.
        before["assignments"] = [
            restored if a["id"] == assignment["id"] else a for a in before["assignments"]
        ]
        save("identity-assignments.json", before)
        record = ROOT / "reports/evidence/permission-exercise.json"
        if record.exists():
            info = json.loads(record.read_text())
            info["restored"] = True
            info["restored_assignment_id"] = restored["id"]
            save("permission-exercise.json", info)


if __name__ == "__main__":
    main()
