# Work with existing resources

Use import discovery to generate configuration candidates from an existing
workspace.

## Discover

```powershell
datamuru import discover --config datamuru.yml --output json
```

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

The alpha generator produces workspace shape. It does not write state or
guarantee conflict-free adoption.

## Reconcile before live apply

Keep `live-readonly`, validate, and plan each imported catalog separately.
Investigate all create, update, and destroy actions before enabling mutation.
