# Scoped identities and permission exercise

| Identity | Scope and permissions | Why |
|---|---|---|
| lab5-training | Reader on the ML workspace; Blob Data Contributor only on the workspace artifact container; AcrPull only on the registry | Read the deployed incumbent, read input data, persist training outputs, and pull the runtime image. No model registration or endpoint write role. |
| lab5-serving | Blob Data Reader only on the artifact container; AcrPull on registry; Monitoring Metrics Publisher on existing App Insights | Read the registered model and image and publish telemetry. Cannot overwrite training data or register/deploy models. |
| lab5-ci | AzureML Data Scientist on the workspace; Blob Data Contributor on artifact container; AcrPush on registry; Managed Identity Operator on the serving identity only | Submit jobs, register candidate artifacts, deploy staging, push images, and attach the serving identity. It cannot assign arbitrary RBAC roles or modify shared compute through the ML Data Scientist role. |

The developer's interactive identity performs the initial bootstrap of identities, narrowly scoped role assignments and compute. It is not the runtime training or serving identity. No account key is copied into the job or image.

The registry and artifact container are existing shared lab resources; scope is at that container/registry rather than subscription. A dedicated per-lab container would reduce training write scope further, at the cost of configuring a separate ML datastore and grants. The broad workspace ML Data Scientist role is constrained to the existing workspace; a production system should split its staging deployment permissions into a custom role and separate workspace.

Actual principal IDs and role assignments are recorded in reports/evidence/identity-assignments.json. The permission-removal exercise result will be recorded separately after the managed runtime is available; a role table alone does not satisfy that exercise.
