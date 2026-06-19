# Enterprise project structure

Enterprise DataMuru projects should be boring to navigate. A reviewer should be
able to open the repository, identify the platform, environment, workspace,
governance scope, and migration intent without asking the original author.

This guide defines the recommended file-system convention for teams managing
multiple workspaces and providers.

## Recommended layout

```text
datamuru.yml
providers/
  databricks.azure.yml
  snowflake.enterprise.yml
environments/
  dev.yml
  test.yml
  prod.yml
workspaces/
  databricks/
    dev.us-poc-dev.yml
    prod.finance-prod.yml
  snowflake/
    dev.analytics-dev.yml
    prod.enterprise-prod.yml
governance/
  taxonomy.enterprise.yml
  rbac.enterprise.yml
  masking.enterprise.yml
migrations/
  databricks-to-snowflake/
    dev.us-poc-dev.to.analytics-dev.yml
imports/
  databricks/
    2026-06-19.us-poc-dev.inventory.yml
    2026-06-19.us-poc-dev.grants.catalog.yml
```

## Naming pattern

Use names that sort well and survive handoff.

| File type | Pattern | Example |
| --- | --- | --- |
| Environment | `<environment>.yml` | `prod.yml` |
| Provider | `<provider>.<scope>.yml` | `databricks.azure.yml` |
| Workspace | `<environment>.<workspace-slug>.yml` | `dev.us-poc-dev.yml` |
| Governance | `<domain-or-scope>.<kind>.yml` | `enterprise.rbac.yml` |
| Import result | `<date>.<workspace-slug>.<scope>.yml` | `2026-06-19.us-poc-dev.inventory.yml` |
| Migration | `<source>.to.<target>.yml` | `us-poc-dev.to.analytics-dev.yml` |

Keep slugs lowercase, hyphenated, and stable:

```text
finance-prod
commercial-dev
us-poc-dev
enterprise-analytics
```

Avoid names that depend on a person, temporary experiment, or ticket number.

## Root config contract

`datamuru.yml` should stay small. It should point to the active environment,
state backend, provider family, and feature posture.

```yaml
project:
  name: enterprise-governance
  version: 0.1.0
  description: Enterprise governed data infrastructure
  edition: enterprise
  provider: databricks

default_environment: dev

environments:
  - name: dev
    config: environments/dev.yml
  - name: prod
    config: environments/prod.yml

provider:
  name: databricks
  cloud: azure
  config: providers/databricks.azure.yml

features:
  governance: true
  multi_workspace: true
  identity_management: true
  hosted_control_plane: false
```

## Multi-workspace rule

Use one workspace declaration per physical workspace. Do not merge unrelated
workspaces into one YAML file just because they share a provider.

Good:

```text
workspaces/databricks/dev.us-poc-dev.yml
workspaces/databricks/dev.eu-poc-dev.yml
workspaces/databricks/prod.finance-prod.yml
```

Poor:

```text
workspaces/all-dev-workspaces.yml
```

The first pattern lets DataMuru target, import, compare, and promote one
workspace without forcing a scan of everything else.

## Import output rule

Large enterprises should never run an unbounded import as their first step.
Use a staged import:

```powershell
datamuru import discover --config datamuru.yml --catalog finance_raw
datamuru import discover --config datamuru.yml --catalog finance_raw --include-grants --grant-scope catalog
datamuru import generate --config datamuru.yml --catalog finance_raw --include-identities --include-grants --grant-scope catalog --suite-out imports/databricks
```

Only use `--grant-scope all` after a reviewer chooses the catalog and object
budget:

```powershell
datamuru import discover --config datamuru.yml --catalog finance_raw --include-grants --grant-scope all --max-grant-objects 100
```

This is the enterprise-safe path: inventory first, catalog-level grants second,
deep object grants last.

## Review checklist

- Every provider file is named by provider and cloud or account scope.
- Every workspace file is named by environment and workspace slug.
- Generated import files include a date and scan scope.
- RBAC, taxonomy, and masking files are separated from workspace topology.
- Migration files name both source and target.
- No command requires scanning every workspace before producing a useful result.
