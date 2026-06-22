# Import an existing workspace

This tutorial discovers supported Databricks resources and generates a starter
workspace YAML file. Import is a review workflow, not automatic ownership
transfer.

Targeted adoption is available for selected supported resources after review.
Automatic broad ownership adoption across an entire workspace is not available.

## Prerequisites

- `live-readonly` or `live-apply` execution mode;
- successful workspace connectivity;
- exactly one workspace declaration in scope.

## Discover resources

```powershell
datamuru import discover --config datamuru.yml
```

By default, DataMuru filters common system catalogs, schemas, and groups.

For machine-readable output:

```powershell
datamuru import discover --config datamuru.yml --output json
```

## Generate a starter file

Select catalogs explicitly:

```powershell
datamuru import generate `
  --config datamuru.yml `
  --catalog existing_sales `
  --catalog existing_marketing `
  --out .\workspaces\imported-review.yml
```

Add `--include-groups` only if you intend to review group references.

## Generate an Enterprise review suite

For enterprise brownfield onboarding, generate all review files together:

```powershell
datamuru import generate `
  --config datamuru.yml `
  --catalog existing_sales `
  --suite-out .\import-review
```

This writes:

- `import-review\workspaces\imported-dev.yml`
- `import-review\governance\rbac.imported.yml`
- `import-review\governance\taxonomy.imported.yml`
- `import-review\governance\masking.imported.yml`

The suite attempts to include identity context and grant-derived RBAC when the
workspace supports account SCIM and a SQL warehouse is configured. If those
capabilities are unavailable, DataMuru still writes the catalog/schema review
file and leaves the missing enterprise sections empty for manual curation.

## Review before adoption

Inspect the generated file for:

- system or vendor-managed objects;
- resources owned by another team;
- names that should remain external references;
- missing managed locations or governance intent;
- groups that DataMuru should not manage.

Generated YAML describes discovered shape. It does not establish that DataMuru
has permission or authority to mutate every object.

## Preview state adoption

1. Back up the existing local state file.
2. Keep `execution_mode: live-readonly`.
3. Move the reviewed YAML into the intended workspace scope.
4. Run validation, a targeted plan, and an adoption preview.

```powershell
datamuru validate --config datamuru.yml
datamuru plan --config datamuru.yml --target catalog:existing_sales
datamuru import adopt --config datamuru.yml --target catalog:existing_sales
```

The preview must show only resources you intend DataMuru to manage. Adoption is
blocked if a selected resource is missing live, differs from the declaration,
or already has conflicting local state.

## Commit ownership to state

```powershell
datamuru import adopt `
  --config datamuru.yml `
  --target catalog:existing_sales `
  --auto-approve
```

Expected result:

```text
Adopted 3 resources into state.
```

Re-run the targeted plan. Adopted resources should be no-op:

```powershell
datamuru plan --config datamuru.yml --target catalog:existing_sales
```

Adoption writes local state only. It does not change Databricks resources.
Do not switch to `live-apply` until the resulting plan contains only understood
actions.

## Include system objects only for diagnosis

`--include-system` can expose `system`, `samples`, `workspace`,
`information_schema`, `admins`, and `users`. Do not adopt or delete these
objects merely because they appear in discovery.
