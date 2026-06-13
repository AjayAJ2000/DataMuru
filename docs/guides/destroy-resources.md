# Destroy resources safely

Destroy removes state-managed resources and can delete supported live
Databricks objects.

!!! danger "Destructive operation"
    A catalog or schema can contain data and downstream dependencies. DataMuru
    cannot determine every business consequence.

## Plan first

Remove the declaration or select the state-managed target, then run:

```powershell
datamuru plan --config datamuru.yml --target schema:analytics.sandbox
```

Confirm the plan contains only the intended destroy.

## Require explicit confirmation

```powershell
datamuru destroy `
  --config datamuru.yml `
  --target schema:analytics.sandbox `
  --confirm-destroy
```

## Identity deletion is separately protected

Managed identity deletion requires `allow_delete: true` on the identity
resource. System groups cannot be deleted. Identity lifecycle is an Enterprise
capability.

## Recover from an unintended state change

If only local state changed, restore the state backup and re-plan. If the live
resource was deleted, recovery depends on Databricks and storage-level backup
capabilities. Do not assume apply or destroy is transactional.
