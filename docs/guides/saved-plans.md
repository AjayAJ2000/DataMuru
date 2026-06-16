# Use saved plans

Saved plans separate review from execution.

In `v0.2` and later, a saved plan is more than a raw list of changes. It also
contains metadata that ties the artifact to the project, provider, environment,
target, and configuration fingerprint that produced it.

## Save a plan

```powershell
datamuru plan --config datamuru.yml --out .\plans\dev-plan.json
```

You can combine `--out` with `--target`.

The saved artifact has this top-level shape:

```json
{
  "metadata": {
    "schema_version": "datamuru.saved_plan.v1",
    "environment": "dev",
    "target": "catalog:analytics",
    "config_fingerprint": "..."
  },
  "plan": {
    "environment": "dev",
    "changes": []
  }
}
```

## Review and protect the artifact

Treat a saved plan as an operational artifact:

- store it in an access-controlled CI artifact store;
- do not edit it manually;
- verify its environment and resource addresses;
- do not reuse it after configuration, provider, or state changes.

## Apply the saved plan

```powershell
datamuru apply --config datamuru.yml --plan .\plans\dev-plan.json --auto-approve
```

DataMuru validates saved-plan structure, schema version, environment, provider,
project name, and configuration fingerprint. It raises `DMR-PLAN-1001` when it
cannot safely load or apply the artifact.

## Regenerate instead of repairing

If a saved plan is stale or invalid, create a new plan. Do not patch JSON to
bypass validation. The stale-plan check is intentional: it prevents a reviewed
artifact from being applied after the YAML project, workspace declarations,
provider settings, or governance files have changed.
