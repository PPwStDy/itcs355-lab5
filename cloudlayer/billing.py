"""Capture actual scoped billing; an empty result is explicitly pending, never zero cost."""

from __future__ import annotations

import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from cloudlayer.manage import SUB, save


def main():
    query = {
        "type": "ActualCost",
        "timeframe": "Custom",
        "timePeriod": {"from": "2026-10-16T00:00:00Z", "to": "2026-10-18T00:00:00Z"},
        "dataset": {
            "granularity": "Daily",
            "aggregation": {"cost": {"name": "Cost", "function": "Sum"}},
            "grouping": [
                {"type": "Dimension", "name": "ResourceId"},
                {"type": "Dimension", "name": "ResourceType"},
            ],
            "filter": {
                "and": [
                    {"tags": {"name": "course", "operator": "In", "values": ["itcs355"]}},
                    {"tags": {"name": "lab", "operator": "In", "values": ["5"]}},
                ]
            },
        },
    }
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "query.json"
        path.write_text(json.dumps(query))
        output = subprocess.run(
            [
                "az",
                "rest",
                "--method",
                "post",
                "--url",
                f"https://management.azure.com/subscriptions/{SUB}/providers/Microsoft.CostManagement/query?api-version=2023-03-01",
                "--body",
                "@" + str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    properties = json.loads(output.stdout)["properties"]
    if properties.get("nextLink"):
        raise ValueError("Billing is paginated; capture all pages before claiming a total")
    rows = properties.get("rows", [])
    save(
        "lab5-billing.json",
        dict(
            captured_at=datetime.now(timezone.utc).isoformat(),
            source="Azure Cost Management ActualCost",
            query=query,
            result=properties,
            status="available_unfinalized" if rows else "pending_provider_billing",
            finalized=False,
        ),
    )
    print(
        "Captured billed rows; still recheck after 24 hours"
        if rows
        else "No Lab 5 billed rows published yet; actual cost remains pending"
    )


if __name__ == "__main__":
    main()
