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
  --include-grants
```

Grant discovery can take longer than catalog/schema discovery because DataMuru
uses the SQL warehouse to inspect grants for every catalog and schema in scope.
If the warehouse is cold or the workspace has many schemas, scope the run with
`--catalog` first.

## Generate selected configuration

```powershell
datamuru import generate `
  --config datamuru.yml `
  --catalog analytics `
  --out .\workspaces\analytics-import.yml
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
