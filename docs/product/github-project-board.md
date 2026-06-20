# DataMuru GitHub Project board

This page defines the private user-level GitHub Project that should track the
DataMuru product roadmap. The board should be private because it will include
commercial packaging, Enterprise roadmap, customer feedback, and release
planning notes that do not belong in the public OSS issue tracker.

## Recommended project

| Setting | Value |
| --- | --- |
| Owner | AjayAJ2000 user account |
| Visibility | Private |
| Name | DataMuru Product Roadmap |
| Template | Team planning or Feature roadmap |
| Primary view | Board |
| Secondary views | Table, Roadmap |

## Workflow columns

Use these status values:

| Status | Meaning |
| --- | --- |
| Inbox | Captured but not shaped |
| Discovery | Product or technical research is active |
| Ready | Scope is clear enough to build |
| In progress | Implementation is active |
| Validate | Local, integration, docs, or enterprise testing |
| Release | Packaging, docs, CI, and PyPI/GitHub Pages work |
| Done | Released or intentionally closed |

## Fields

Create these custom fields:

| Field | Type | Options |
| --- | --- | --- |
| Area | Single select | Core, Provider, Governance, Import, UI, Docs, Enterprise, Website, Release |
| Provider | Single select | Provider-agnostic, Databricks, Snowflake, AWS, Azure, GCP |
| Edition | Single select | OSS, Enterprise, Both |
| Customer impact | Single select | Evaluation, Production, Security, Cost, Developer experience |
| Risk | Single select | Low, Medium, High |
| Release target | Text | Example: `0.4.0a0` |
| Evidence link | Text | PR, docs, CI, demo, test output, or release link |

## Initial backlog

Create these items first:

| Title | Area | Provider | Edition | Customer impact | Risk | Release target |
| --- | --- | --- | --- | --- | --- | --- |
| Resumable enterprise import jobs | Import | Provider-agnostic | Enterprise | Cost | High | 0.4.0a0 |
| Import progress model with ETA and checkpoints | Import | Provider-agnostic | Both | Developer experience | High | 0.4.0a0 |
| Databricks grant scan budgets by object type | Provider | Databricks | Both | Cost | Medium | 0.4.0a0 |
| Local UI import review workspace | UI | Provider-agnostic | Both | Evaluation | Medium | 0.4.0a0 |
| Databricks-to-Snowflake mapping draft | Provider | Snowflake | Enterprise | Production | High | 0.4.0a0 |
| Snowflake live discovery spike | Provider | Snowflake | Enterprise | Evaluation | High | 0.4.0a0 |
| Enterprise file naming convention enforcement | Core | Provider-agnostic | Both | Developer experience | Medium | 0.4.0a0 |
| GitHub Projects issue export command | Core | Provider-agnostic | Both | Developer experience | Low | 0.4.0a0 |
| Hosted control plane product architecture | Enterprise | Provider-agnostic | Enterprise | Production | High | 0.5.0a0 |
| Enterprise purchase and license activation flow | Enterprise | Provider-agnostic | Enterprise | Production | High | 0.5.0a0 |
| Enterprise activation readiness preflight | Enterprise | Provider-agnostic | Enterprise | Production | Medium | 0.5.0a0 |

## Labels

Use these GitHub issue labels:

- `area/core`
- `area/provider`
- `area/governance`
- `area/import`
- `area/ui`
- `area/docs`
- `edition/oss`
- `edition/enterprise`
- `provider/databricks`
- `provider/snowflake`
- `risk/high`
- `release/0.4.0a0`
- `release/0.5.0a0`

## Automation

Start simple:

- new issues go to `Inbox`;
- issues assigned to a milestone move to `Ready`;
- linked pull requests move the item to `In progress`;
- merged pull requests move the item to `Validate`;
- released tags move manually to `Done`.

Avoid over-automation until the team has used the board for at least two
release cycles.
