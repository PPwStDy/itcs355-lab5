# Serving manifest access — safer alternative

The actual initializer pulled the container image successfully, then received HEAD 403 AuthorizationPermissionMismatch for an endpoint model-manifest blob in the workspace storage account’s `azureml` container. The serving identity already reads the separate workspaceblobstore model-artifact container.

Automatic approval review rejected replacing that read grant with account-wide Storage Blob Data Reader because it would expand access across shared storage beyond the approved scope. That rejected action was not executed.

Prepared alternative: keep the existing artifact-container grant and add read access only on container `azureml`, with an ABAC condition allowing blob reads only for `itcs355-lab5-staging_blue_model_config_map.json_*`. Deny blob listing through this new assignment. The condition does not grant reads of other endpoints’ manifests or other containers. Remove this exact recorded grant with the other Lab 5 grants at teardown. No account-wide role is requested.

Microsoft condition syntax: https://learn.microsoft.com/en-us/azure/storage/blobs/storage-auth-abac-examples .

The user approved the exact manifest-only alternative. It was applied successfully and recorded in serving-manifest-reader.json and identity-assignments.json for teardown.

The retry succeeded with the conditional grant: model download and user-container startup completed, and a targeted invocation returned the expected registered model. Exact logs and response are retained separately.
