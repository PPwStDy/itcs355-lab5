"""Test the gated model on staging while automatic endpoint traffic stays at zero."""

from __future__ import annotations
import json
import tempfile
from pathlib import Path
from io import StringIO
import yaml
from azure.ai.ml import load_online_deployment
from cloudlayer.manage import ml_client, settings, ROOT, save
from cloudlayer.lab5_runtime import deployment_spec


def main():
    m = ml_client()
    root = json.loads((ROOT / "reports/evidence/managed-run.json").read_text())["name"]
    parent = m.jobs.get(root)
    assert parent.tags.get("course") == "itcs355" and parent.tags.get("lab") == "5"
    jobs = list(m.jobs.list(parent_job_name=root))
    register = next(j for j in jobs if j.display_name == "register")
    assert register.status == "Completed"
    with tempfile.TemporaryDirectory() as folder:
        m.jobs.download(register.name, download_path=folder, output_name="result")

        def read(name):
            paths = list(Path(folder).rglob(name))
            if len(paths) != 1:
                raise RuntimeError("Missing or ambiguous " + name)
            return json.loads(paths[0].read_text())

        registered = read("registered.json")
        assert read("gate.json")["passed"] is True
        ep = m.online_endpoints.get("itcs355-lab5-staging")
        assert ep.tags.get("course") == "itcs355" and ep.tags.get("lab") == "5"
        assert not any((ep.traffic or {}).values()), "Preflight requires zero automatic traffic"
        spec = deployment_spec(registered, settings()["runtime_env"]["SERVING_IMAGE"])
        deployment = load_online_deployment(source=StringIO(yaml.safe_dump(spec)))
        deployment._validate()
        save(
            "deployment-preflight.json",
            dict(model=registered, status="Starting", automatic_traffic=ep.traffic),
        )
        try:
            result = m.online_deployments.begin_create_or_update(deployment).result()
        except Exception as error:
            save(
                "deployment-preflight.json",
                dict(
                    model=registered,
                    status="Failed",
                    automatic_traffic=ep.traffic,
                    error=str(error),
                ),
            )
            raise
        save(
            "deployment-preflight.json",
            dict(model=registered, status=result.provisioning_state, automatic_traffic=ep.traffic),
        )
        request = Path(folder) / "request.json"
        request.write_text(
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
            m.online_endpoints.invoke(
                endpoint_name=ep.name, deployment_name="blue", request_file=str(request)
            )
        )
        assert (
            response["model_version"] == registered["version"] and 0 <= response["probability"] <= 1
        )
        save(
            "deployment-preflight.json",
            dict(
                model=registered,
                status=result.provisioning_state,
                automatic_traffic=ep.traffic,
                response=response,
            ),
        )
        print("Serving preflight succeeded: " + json.dumps(response), flush=True)


if __name__ == "__main__":
    main()
