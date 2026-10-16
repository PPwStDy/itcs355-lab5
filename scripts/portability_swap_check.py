"""Real second-provider round trip and inference, with separate secondary configuration."""

import argparse
import hashlib
import json
import sys
import tempfile
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cloudlayer.factory import get_adapter
from src import config


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--second-provider", choices=["aws", "gcp", "azure"], required=True)
    ap.add_argument("--blob-uri", required=True)
    ap.add_argument("--region", required=True)
    ap.add_argument("--endpoint", required=True)
    ap.add_argument("--out", type=Path, default=Path("reports/evidence/portability.json"))
    args = ap.parse_args()
    primary = config.load(strict=False)
    if primary.provider == args.second_provider:
        raise ValueError("Second provider must differ from primary")
    adapter = get_adapter(
        replace(primary, provider=args.second_provider, blob_uri=args.blob_uri, region=args.region)
    )
    with tempfile.TemporaryDirectory() as directory:
        source, back = Path(directory) / "probe.txt", Path(directory) / "back.txt"
        source.write_text("itcs355 lab5 portability probe\n")
        uri = adapter.upload(str(source), "lab5/portability-probe.txt")
        adapter.download(uri, str(back))
        assert source.read_bytes() == back.read_bytes(), "Downloaded bytes differ"
        response = adapter.invoke(
            args.endpoint,
            dict(
                temp_c=78.4,
                vibration_mm_s=3.1,
                pressure_kpa=315.2,
                hours_since_service=4200,
                load_pct=68,
                ambient_humidity=55,
            ),
        )
        evidence = dict(
            timestamp=datetime.now(timezone.utc).isoformat(),
            primary=primary.provider,
            secondary=args.second_provider,
            object_sha256=hashlib.sha256(back.read_bytes()).hexdigest(),
            uploaded_uri=uri,
            response=response,
            simulated=False,
        )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(evidence, indent=2) + "\n")
    print("Second-provider byte round trip and inference passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
