# Root configuration

`datamuru.yml` is the project entry point.

## `project`

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | string | yes | Project identifier |
| `version` | string | yes | Project configuration version |
| `description` | string | yes | Human-readable purpose |
| `edition` | string | yes | `open-source` or `enterprise` |
| `provider` | string | yes | Provider name; currently `databricks` |

## `environments`

A list of objects with `name` and `config`. `default_environment` must match one
of the names.

## `features`

Boolean fields:

- `governance`
- `data_mesh`
- `ingestion`
- `modeling`
- `observability`
- `compliance_reporting`
- `multi_workspace`
- `hosted_control_plane`
- `identity_management`

The last four are Enterprise-only. A false value is allowed in OSS.

## `state`

| Field | Description |
| --- | --- |
| `backend` | `local`, `s3`, `azure_blob`, or `gcs`; only local is implemented in the OSS alpha |
| `path` | State file path |

Run `datamuru state inspect --output json` to check backend readiness before
plan or apply workflows. Local state reports `mode: read-write`. Remote backend
values are accepted as a forward-compatible contract for hosted workflows, but
the OSS alpha reports them as `mode: contract-only` and exits nonzero so
automation does not accidentally proceed with an unsupported shared backend.

## `provider`

Contains `name`, `cloud`, and `config`. Supported cloud identifiers are
`azure`, `aws`, and `gcp`; Azure is the first implemented integration target.

## `ai`

Optional mapping reserved for AI-related product integrations. Current values
do not change the core execution loop.

## `enterprise`

Optional mapping for Enterprise extension contracts. OSS currently supports an
activation preflight shape:

| Field | Required | Description |
| --- | --- | --- |
| `activation.organization` | yes | Customer or organization name for onboarding |
| `activation.contact_email` | yes | Activation and support contact |
| `activation.control_plane_url` | yes | Expected Enterprise control plane URL |
| `activation.tenant_id` | yes | Tenant identifier requested for activation |
| `activation.deployment_region` | yes | Preferred control plane region |
| `activation.license_key_env` | yes | Environment variable that stores the license key |
| `activation.purchase_reference` | no | Purchase order, subscription, or contract reference |
| `activation.support_plan` | no | Commercial support plan label |

Use `datamuru enterprise activation check` to validate the shape before handing
the project to an Enterprise onboarding workflow.
