# Work with existing resources

Use import discovery to generate configuration candidates from an existing
workspace.

## Discover

```powershell
datamuru import discover --config datamuru.yml --output json
```

For interactive use, omit `--output json` to see a progress bar and the current
provider stage:

```powershell
datamuru import discover --config datamuru.yml
```

In enterprise workspaces, start with one catalog before requesting grants:

```powershell
datamuru import discover `
  --config datamuru.yml `
  --catalog analytics `
  --include-identities `
  --include-grants `
  --grant-scope catalog
```

Grant discovery can take much longer than catalog/schema discovery because
DataMuru uses the SQL warehouse to inspect grants. The safe enterprise flow is:

1. Discover inventory without grants.
2. Scope to one catalog.
3. Scan catalog-level grants.
4. Scan schema-level or all grants only for the selected catalog.

```powershell
datamuru import discover `
  --config datamuru.yml `
  --catalog analytics `
  --include-grants `
  --grant-scope all `
  --max-grant-objects 100
```

If the estimate exceeds `--max-grant-objects`, DataMuru stops before launching
the expensive SQL grant scan.

## Generate selected configuration

```powershell
datamuru import generate `
  --config datamuru.yml `
  --catalog analytics `
  --out .\workspaces\analytics-import.yml
```

For enterprise review suites, prefer provider-aware file names:

```powershell
datamuru import generate `
  --config datamuru.yml `
  --catalog analytics `
  --include-identities `
  --include-grants `
  --grant-scope catalog `
  --suite-out .\imports `
  --suite-layout enterprise
```

This writes files such as:

```text
imports/
  workspaces/databricks.dev.us-poc-dev.analytics.workspace.yml
  governance/databricks.dev.us-poc-dev.analytics.rbac.yml
  governance/databricks.dev.us-poc-dev.analytics.taxonomy.yml
  governance/databricks.dev.us-poc-dev.analytics.masking.yml
```

## Review ownership

For each resource, decide whether it is:

- **managed** by this DataMuru project;
- an **existing reference** used by grants or dependencies;
- **external** and intentionally outside DataMuru.

The generator produces workspace shape. It does not write state.

## Preview and commit adoption

Keep `live-readonly`, validate, and plan each imported catalog separately:

```powershell
datamuru import adopt --config datamuru.yml --target catalog:analytics
```

When the preview has no blockers:

```powershell
datamuru import adopt `
  --config datamuru.yml `
  --target catalog:analytics `
  --auto-approve
```

Adoption is atomic for the selected targets. DataMuru does not write partial
state when any selected resource is missing or has a fingerprint conflict.
Investigate all later create, update, and destroy actions before enabling live
mutation.
