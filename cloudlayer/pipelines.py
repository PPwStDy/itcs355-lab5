"""Compile the portable stages to an actual Azure ML pipeline DAG."""

from __future__ import annotations
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_spec(path=None):
    return yaml.safe_load(Path(path or ROOT / "pipeline/pipeline.yaml").read_text())


def compile_azure(settings, *, bootstrap=False, forced_incumbent=None):
    from azure.ai.ml import Input, Output, command
    from azure.ai.ml.entities import PipelineJob, ManagedIdentityConfiguration

    common = dict(
        code=str(ROOT),
        environment=settings["environment"],
        compute=settings["compute"],
        environment_variables={k: str(v) for k, v in settings["runtime_env"].items()},
        tags={"course": "itcs355", "lab": "5"},
    )
    jobs = {}
    previous = None
    for stage in ("ingest", "validate", "train", "evaluate", "register", "deploy_staging"):
        identity = (
            settings["ci_client_id"]
            if stage in ("register", "deploy_staging")
            else settings["training_client_id"]
        )
        inputs = (
            {
                "source": Input(
                    type="uri_file",
                    path=settings.get("source_asset", str(ROOT / "data/raw/sensors.csv")),
                )
            }
            if previous is None
            else {
                "previous": Input(
                    type="uri_folder", path=f"${{{{parent.jobs.{previous}.outputs.result}}}}"
                )
            }
        )
        flag = "--source ${{inputs.source}}" if previous is None else "--input ${{inputs.previous}}"
        extra = " --bootstrap" if bootstrap else ""
        if forced_incumbent is not None:
            extra += f" --incumbent {float(forced_incumbent)}"
        step_common = dict(common)
        step_common["environment_variables"] = dict(
            common["environment_variables"], AZURE_CLIENT_ID=identity
        )
        job = command(
            **step_common,
            identity=ManagedIdentityConfiguration(client_id=identity),
            inputs=inputs,
            outputs={"result": Output(type="uri_folder", mode="rw_mount")},
            command=f"python -m cloudlayer.lab5_runtime --stage {stage} {flag} --out ${{{{outputs.result}}}}{extra}",
            display_name="lab5-" + stage,
            is_deterministic=False,
        )
        jobs[stage] = job
        previous = stage
    return PipelineJob(
        jobs=jobs,
        display_name="Lab 5 gated maintenance pipeline",
        experiment_name="itcs355-lab5",
        tags={"course": "itcs355", "lab": "5"},
        settings={"continue_on_step_failure": False, "force_rerun": True},
    )


def compile_for(provider, spec=None):
    if provider != "azure":
        raise ValueError(
            "The managed pipeline uses the primary provider; the second-provider scope is upload/download/invoke only"
        )
    import json

    return compile_azure(json.loads((ROOT / "reports/cloud-settings.json").read_text()))
