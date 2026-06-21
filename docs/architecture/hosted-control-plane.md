# Hosted control plane architecture

The hosted control plane is the Enterprise service boundary around the OSS
DataMuru package. OSS remains local-first: it validates configuration, builds
plans, runs provider workflows, and exports redacted contracts. The hosted
control plane adds tenant management, shared execution, team review, scheduling,
remote state extensions, and audit evidence.

## Architecture contract

Export the current reference architecture as JSON:

```powershell
datamuru enterprise control-plane architecture `
  --config datamuru.yml `
  --out .\.datamuru\control-plane\architecture.json `
  --output json
```

The contract schema is `datamuru.hosted_control_plane_architecture.v1`. It is a
planning and implementation artifact, not a provisioning command.

## Core components

| Component | Boundary | Responsibility |
| --- | --- | --- |
| OSS CLI and Python API | Local | Validate config, build plans, generate contracts, and run local workflows |
| Hosted control plane API | Hosted | Accept activation contracts, manage tenants, schedule jobs, and expose team workflows |
| Job runner | Hosted runtime | Execute approved import, plan, evidence, and apply jobs with tenant-scoped credentials |
| State extension | Enterprise extension | Provide shared state locking, concurrency control, and remote backend adapters |
| Secret source | Customer or hosted secret manager | Resolve license keys and provider credentials without embedding secret values |
| Audit evidence store | Hosted | Persist redacted activation, plan, apply, import, and support evidence |

## Data flows

- Activation handoff: OSS exports activation bundle, control-plane contract, and
  activation evidence for onboarding.
- Scheduled import: hosted scheduler dispatches scoped import jobs with budgets
  and checkpoint locations.
- Approved apply: review workflow submits a saved plan, approval metadata, and
  provider credential handle to the runner.
- Evidence export: audit evidence store emits redacted JSON reports for
  operators or support.

## Trust boundaries

- Local operator machine to hosted control plane API.
- Hosted control plane API to job runner queue.
- Job runner to customer cloud provider APIs.
- Hosted state extension to durable state backend.
- Secret manager handle to runtime secret material.
- Audit evidence store to exported support artifacts.

## Extension points

- `state_backend`: remote backend adapters and locking semantics.
- `identity_provider`: tenant users, groups, service principals, and approval
  roles.
- `secret_manager`: environment variable or secret-handle references only.
- `provider_adapter`: DataMuru provider interface for observation, desired
  resources, diagnostics, and apply.
- `audit_sink`: redacted evidence records and exportable JSON reports.

## Accepted decisions

| ID | Decision |
| --- | --- |
| HCP-001 | Keep OSS CLI local-first and contract-producing |
| HCP-002 | Treat remote state as an Enterprise extension boundary before implementation |
| HCP-003 | Use redacted JSON contracts for activation and evidence handoff |
| HCP-004 | Separate hosted orchestration from provider mutation |

## Implementation backlog

| ID | Phase | Work |
| --- | --- | --- |
| HCP-B1 | Activation | Tenant and entitlement registry |
| HCP-B2 | Execution | Hosted job runner queue |
| HCP-B3 | State | Remote state extension |
| HCP-B4 | Audit | Audit evidence store |
| HCP-B5 | Collaboration | Team review workflow |

## Non-goals

- Do not embed a web server in the OSS CLI package.
- Do not store license keys, provider tokens, or private keys in project YAML.
- Do not make remote state writes from OSS until a backend extension owns
  locking and concurrency.
- Do not bypass plan review for hosted apply workflows.
