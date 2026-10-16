"""Measure a warm idle training node versus actual scale-to-zero before deleting it."""

from __future__ import annotations
import json
import time
from datetime import datetime, timezone
from cloudlayer.manage import ROOT, COMPUTE, RG, WS, az, save


def nodes():
    return az("ml", "compute", "list-nodes", "-n", COMPUTE, "-g", RG, "-w", WS, "-o", "json")


def main():
    az("ml", "compute", "update", "-n", COMPUTE, "-g", RG, "-w", WS,
       "--min-instances", "1", "-o", "json")
    before = nodes()
    if len(before) != 1:
        raise RuntimeError("Warm-node baseline unavailable; do not claim measured savings")
    az("ml", "compute", "update", "-n", COMPUTE, "-g", RG, "-w", WS,
       "--min-instances", "0", "--idle-time-before-scale-down", "60", "-o", "json")
    started = time.monotonic()
    while time.monotonic() - started < 300:
        after = nodes()
        if not after:
            break
        time.sleep(15)
    else:
        raise RuntimeError("Scale-to-zero was configured but not observed")
    prices = json.loads((ROOT / "reports/evidence/planning-prices.json").read_text())
    hourly = max(x["retailPrice"] for x in prices["prices"]) * prices["exchange"]["usd_thb"]
    result = dict(
        captured_at=datetime.now(timezone.utc).isoformat(),
        optimisation="training cluster min_instances 1 to 0",
        before_idle_node_count=len(before),
        after_idle_node_count=0,
        configured_idle_seconds=60,
        observed_scale_down_seconds=round(time.monotonic() - started, 2),
        avoided_idle_capacity_thb_per_hour=hourly,
        limitation="Observed node removal times verified retail price; actual invoice savings are pending billing.",
    )
    save("optimisation.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
