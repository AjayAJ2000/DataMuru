# Use saved plans

Saved plans separate review from execution.

## Save a plan

```powershell
datamuru plan --config datamuru.yml --out .\plans\dev-plan.json
```

You can combine `--out` with `--target`.

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

DataMuru validates saved-plan structure and raises `DMR-PLAN-1001` when it
cannot safely load the artifact.

## Regenerate instead of repairing

If a saved plan is stale or invalid, create a new plan. Do not patch JSON to
bypass validation.
