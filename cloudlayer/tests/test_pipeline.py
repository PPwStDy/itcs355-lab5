from cloudlayer.pipelines import compile_azure


def test_native_pipeline_has_real_dependencies_and_scoped_identities():
    cfg = dict(
        environment="azureml:lab5:1",
        compute="lab5-cpu",
        training_client_id="11111111-1111-1111-1111-111111111111",
        ci_client_id="22222222-2222-2222-2222-222222222222",
        source_asset="azureml:lab5-sensors:1",
        runtime_env={},
    )
    job = compile_azure(cfg, bootstrap=True)
    assert job._validate().passed
    stages = ["ingest", "validate", "train", "evaluate", "register", "deploy_staging"]
    assert set(job.jobs) == set(stages)
    for before, after in zip(stages, stages[1:]):
        assert before in job.jobs[after].inputs["previous"].path
    assert job.jobs["train"].identity.client_id == cfg["training_client_id"]
    assert job.jobs["register"].identity.client_id == cfg["ci_client_id"]
    assert job.settings.continue_on_step_failure is False


def test_model_version_satisfies_azure_integer_constraint():
    from cloudlayer.lab5_runtime import model_version

    for run_id in ("pipeline-child-uuid", "run_with_underscores", "manual"):
        version = model_version(run_id)
        assert version.isdecimal() and 0 < int(version) < 2**31
        assert model_version(run_id) == version
    assert model_version("a") != model_version("b")


def test_actual_deployment_spec_passes_installed_azure_schema():
    from io import StringIO
    import yaml
    from azure.ai.ml import load_online_deployment
    from cloudlayer.lab5_runtime import deployment_spec

    spec = deployment_spec(
        {"id": "/subscriptions/example/models/itcs355-lab5/versions/42", "version": "42"},
        "example.azurecr.io/model:sha",
    )
    deployment = load_online_deployment(source=StringIO(yaml.safe_dump(spec)))
    deployment._validate()
    assert deployment.model == "itcs355-lab5:42"
