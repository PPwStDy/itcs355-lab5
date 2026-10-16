"""Read-only verification; never delete resources while claiming to inspect them."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cloudlayer.manage import inventory

if __name__ == "__main__":
    remaining = inventory()
    print(json.dumps(remaining, indent=2))
    raise SystemExit(1 if any(remaining.values()) else 0)
