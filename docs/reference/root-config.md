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

## `provider`

Contains `name`, `cloud`, and `config`. Supported cloud identifiers are
`azure`, `aws`, and `gcp`; Azure is the first implemented integration target.

## `ai`

Optional mapping reserved for AI-related product integrations. Current values
do not change the core execution loop.
