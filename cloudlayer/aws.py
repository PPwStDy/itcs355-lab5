"""Second-provider seam: S3 object round trips and a SageMaker inference endpoint."""

from __future__ import annotations
import json
from pathlib import Path
from urllib.parse import urlparse
from cloudlayer.base import CloudAdapter


class AwsAdapter(CloudAdapter):
    def _client(self, service):
        import boto3

        return boto3.client(service, region_name=self.cfg.region)

    @staticmethod
    def _location(uri):
        parsed = urlparse(uri)
        if parsed.scheme != "s3" or not parsed.netloc:
            raise ValueError("Expected an object-storage bucket URI")
        return parsed.netloc, parsed.path.lstrip("/")

    def upload(self, local_path, key):
        bucket, prefix = self._location(self.cfg.blob_uri)
        object_key = "/".join(p for p in (prefix.rstrip("/"), key.lstrip("/")) if p)
        self._client("s3").upload_file(local_path, bucket, object_key)
        return f"s3://{bucket}/{object_key}"

    def download(self, uri, local_path):
        bucket, key = self._location(uri)
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        self._client("s3").download_file(bucket, key, local_path)

    def invoke(self, endpoint, payload):
        result = self._client("sagemaker-runtime").invoke_endpoint(
            EndpointName=endpoint, ContentType="application/json", Body=json.dumps(payload).encode()
        )
        body = json.loads(result["Body"].read())
        # The endpoint must expose the same portable prediction contract.
        if not isinstance(body, dict) or not isinstance(body.get("probability"), (float, int)):
            raise ValueError("Endpoint did not return the portable probability/version contract")
        if (
            isinstance(body["probability"], bool)
            or not 0 <= body["probability"] <= 1
            or not body.get("model_version")
        ):
            raise ValueError("Invalid probability or missing model version")
        return body

    def push_image(self, local_tag):
        raise NotImplementedError(
            "Lab 5 swap intentionally implements only upload, download and invoke"
        )
