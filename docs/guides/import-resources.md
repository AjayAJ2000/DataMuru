# Work with existing resources

Use import discovery to generate configuration candidates from an existing
workspace.

Explicit targeted import and adoption workflows are available for supported
Databricks resources. Automatic broad ownership adoption across a workspace is
not available in this alpha; each adopted target must be reviewed and selected
deliberately.

## Discover

```powershell
datamuru import discover --config datamuru.yml --output json
```

For interactive use, omit `--output json` to see a progress bar and the current
provider stage:

```powershell
datamuru import discover --config datamuru.yml
```

For long enterprise scans, write a progress checkpoint file. This file is safe
to tail, collect as CI evidence, or attach to an operations ticket:

```powershell
datamuru import discover `
  --config datamuru.yml `
  --catalog analytics `
  --include-grants `
  --grant-scope all `
  --progress-checkpoint .\.datamuru\import-progress.json
```

The checkpoint stores the latest structured progress event, including stage,
object type, object name, completed count, and total count when available.

For resumable grant scans, also write a job checkpoint. The job checkpoint stores
completed grant targets and discovered grants, so a later run can skip objects
that were already scanned:

```powershell
datamuru import discover `
  --config datamuru.yml `
  --catalog analytics `
  --include-grants `
  --grant-scope all `
  --progress-checkpoint .\.datamuru\imports\analytics.progress.json `
  --job-checkpoint .\.datamuru\imports\analytics.job.json
```

If the run is interrupted or the warehouse times out, resume with the same scope
and the previous job checkpoint:

```powershell
datamuru import discover `
  --config datamuru.yml `
  --catalog analytics `
  --include-grants `
  --grant-scope all `
  --resume-from .\.datamuru\imports\analytics.job.json `
  --job-checkpoint .\.datamuru\imports\analytics.job.json `
  --progress-checkpoint .\.datamuru\imports\analytics.progress.json
```

Use the same `--catalog`, `--include-grants`, and `--grant-scope` values when
resuming. DataMuru resumes the completed grant-scan objects in the checkpoint;
it still refreshes catalog and schema inventory because that inventory is cheap
and should reflect the current workspace.

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
  --max-grant-objects 100 `
  --max-catalog-grant-objects 5 `
  --max-schema-grant-objects 50
```

If the estimate exceeds `--max-grant-objects`, DataMuru stops before launching
the expensive SQL grant scan. Use the object-type caps when a workspace has a
small number of catalogs but hundreds or thousands of schemas. The current
Databricks alpha enforces `catalog` and `schema` grant budgets. `table`, `view`,
and `volume` budgets are reserved for the next discovery surface.

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
  --max-catalog-grant-objects 20 `
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
