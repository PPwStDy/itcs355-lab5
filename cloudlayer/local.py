"""Explicit filesystem simulation, never presented as a managed cloud execution."""

import json
from pathlib import Path
from cloudlayer.base import LocalAdapter


class LabAdapter(LocalAdapter):
    def register_model(self, model_uri, name, lineage=None):
        path = self.cfg.reports_dir / "local-registry.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                dict(model_uri=model_uri, name=name, lineage=lineage, simulated=True), indent=2
            )
        )
        return str(path)

    def deploy(self, model_ref, endpoint, instance):
        path = self.cfg.reports_dir / "local-deployment.json"
        path.write_text(
            json.dumps(dict(model_ref=model_ref, endpoint=endpoint, simulated=True), indent=2)
        )
        return str(path)
