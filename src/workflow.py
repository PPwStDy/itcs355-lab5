"""Portable training stages. Cloud calls occur only through an injected adapter."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

from src import contracts, data, config
from src.gate import evaluate


def fingerprint(frame):
    return hashlib.sha256(frame.to_csv(index=False, lineterminator="\n").encode()).hexdigest()


def train(source: Path, output: Path, seed=42):
    frame = data.load_raw(source)
    contracts.validate(frame)
    training, validation, test = data.split(frame, seed=seed)
    output.mkdir(parents=True, exist_ok=True)
    source_hash = fingerprint(frame)
    checkpoint = output / "training-checkpoint.joblib"
    completed = 0
    if checkpoint.exists():
        saved = joblib.load(checkpoint)
        if saved["data_sha256"] != source_hash or saved["seed"] != seed:
            raise ValueError("Checkpoint belongs to different data or seed")
        model = saved["model"]
        completed = len(model.estimators_)
    else:
        model = RandomForestClassifier(
            n_estimators=50,
            max_depth=8,
            min_samples_leaf=5,
            random_state=seed,
            n_jobs=-1,
            warm_start=True,
        )
    for trees in range(completed + 50, 201, 50):
        model.set_params(n_estimators=trees)
        model.fit(training[data.FEATURES], training[data.TARGET])
        temporary = output / "training-checkpoint.tmp"
        joblib.dump(dict(model=model, data_sha256=source_hash, seed=seed), temporary)
        temporary.replace(checkpoint)
    joblib.dump(model, output / "model.joblib")
    metrics = dict(
        val_roc_auc=float(
            roc_auc_score(
                validation[data.TARGET], model.predict_proba(validation[data.FEATURES])[:, 1]
            )
        ),
        test_roc_auc=float(
            roc_auc_score(test[data.TARGET], model.predict_proba(test[data.FEATURES])[:, 1])
        ),
        seed=seed,
        code_version=config.code_version(),
        data_sha256=fingerprint(frame),
        validation_sha256=fingerprint(validation),
        model_sha256=hashlib.sha256((output / "model.joblib").read_bytes()).hexdigest(),
    )
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    return metrics


def run(source: Path, output: Path, adapter, *, incumbent=None, bootstrap=False):
    output.mkdir(parents=True, exist_ok=True)
    events = []

    def record(event):
        events.append(event)
        (output / "events.json").write_text(json.dumps(events, indent=2))

    copied = output / "sensors.csv"
    shutil.copyfile(source, copied)
    record("ingest")
    contracts.validate(data.load_raw(copied))
    record("validate")
    metrics = train(copied, output / "candidate")
    record("train")
    decision = evaluate(metrics["val_roc_auc"], incumbent, bootstrap=bootstrap)
    (output / "gate.json").write_text(json.dumps(decision.as_dict(), indent=2))
    record("evaluate:pass" if decision.passed else "evaluate:reject")
    if not decision.passed:
        return decision
    # Registration/deployment remain unreachable on a rejected decision.
    uri = adapter.upload(str(output / "candidate/model.joblib"), "candidate/model.joblib")
    version = adapter.register_model(uri, "itcs355-lab5", lineage=metrics)
    record("register")
    adapter.deploy(version, "itcs355-lab5-staging", "local")
    record("deploy_staging")
    return decision
