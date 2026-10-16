"""Run inside the training identity to prove its workspace read boundary."""

import json
import os
from azure.ai.ml import MLClient
from azure.identity import ManagedIdentityCredential
from azure.core.exceptions import HttpResponseError

client = MLClient(
    ManagedIdentityCredential(client_id=os.environ["AZURE_CLIENT_ID"]),
    os.environ["AZURE_SUBSCRIPTION_ID"],
    os.environ["AZURE_RESOURCE_GROUP"],
    os.environ["AZUREML_WORKSPACE"],
)
try:
    list(client.online_endpoints.list())
except HttpResponseError as error:
    print(
        json.dumps(
            dict(
                operation="list staging endpoints",
                status=error.status_code,
                error_code=getattr(error, "error", None).code
                if getattr(error, "error", None)
                else None,
                identity="lab5-training",
                expected="denied after removing workspace Reader",
            )
        )
    )
    if error.status_code != 403:
        raise
else:
    raise RuntimeError(
        "Workspace read still allowed; removal has not propagated or another grant exists"
    )
