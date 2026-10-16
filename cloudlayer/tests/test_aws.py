import io
import json
from pathlib import Path
from src import config

def test_aws_adapter_roundtrip_uses_returned_uri_and_validates_response(tmp_path, monkeypatch):
    from dataclasses import replace
    from cloudlayer.aws import AwsAdapter

    stored = {}

    class Client:
        def upload_file(self, path, bucket, key):
            stored[(bucket, key)] = Path(path).read_bytes()

        def download_file(self, bucket, key, path):
            Path(path).write_bytes(stored[(bucket, key)])

        def invoke_endpoint(self, **kwargs):
            assert kwargs["EndpointName"] == "endpoint"
            assert json.loads(kwargs["Body"]) == {"temp_c": 80}
            return {"Body": io.BytesIO(b'{"probability":0.1,"model_version":"test-v1"}')}

    adapter = AwsAdapter(
        replace(config.load(strict=False), blob_uri="s3://test-bucket/prefix", region="test")
    )
    monkeypatch.setattr(adapter, "_client", lambda service: Client())
    source = tmp_path / "source"
    source.write_bytes(b"roundtrip")
    uri = adapter.upload(str(source), "nested/key")
    assert uri == "s3://test-bucket/prefix/nested/key"
    back = tmp_path / "nested/back"
    adapter.download(uri, str(back))
    assert back.read_bytes() == source.read_bytes()
    assert adapter.invoke("endpoint", {"temp_c": 80})["model_version"] == "test-v1"
