# Configure a project

A DataMuru project is a directory rooted at `datamuru.yml`. Referenced paths
are resolved relative to that file.

## Recommended layout

```text
project/
├── datamuru.yml
├── environments/
│   └── dev.yml
├── providers/
│   └── databricks.yml
├── workspaces/
│   └── dev.yml
└── governance/
    ├── taxonomy.yml
    ├── rbac.yml
    └── masking.yml
```

## Configure the root file

Use `datamuru.yml` to select the project identity, edition, environments,
features, state backend, and provider reference. Do not put tokens or workspace
resources in this file.

```yaml
project:
  name: analytics-platform
  version: "0.1.0"
  description: Governed analytics platform
  edition: open-source
  provider: databricks

environments:
  - name: dev
    config: ./environments/dev.yml

default_environment: dev

features:
  governance: true
  data_mesh: false
  ingestion: false
  modeling: false
  observability: false
  compliance_reporting: false
  multi_workspace: false
  hosted_control_plane: false
  identity_management: false

state:
  backend: local
  path: ./.datamuru/state-dev.json

provider:
  name: databricks
  cloud: azure
  config: ./providers/databricks.yml
```

## Add workspace intent

DataMuru loads every `*.yml` file under `workspaces/`. Keep only the workspace
files intended for the current project in that directory.

## Add governance definitions

Governance files are optional. If present, they must use these names:

- `governance/taxonomy.yml`
- `governance/rbac.yml`
- `governance/masking.yml`

## Validate every change

```powershell
datamuru validate --config datamuru.yml --strict
```

See [Root configuration](../reference/root-config.md) and
[Workspace configuration](../reference/workspace-config.md) for all fields.
