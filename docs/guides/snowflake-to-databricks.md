# Snowflake to Databricks adoption path

DataMuru can discover Snowflake databases and schemas in `live-readonly` mode
and turn that inventory into a reviewable Databricks mapping draft. The draft
maps Snowflake databases to Databricks catalogs and Snowflake schemas to
Databricks schemas.

This workflow does not copy data, translate SQL, create Databricks objects, or
change either provider.

## Before you start

Use a Snowflake project configured for PAT, browser SSO, or an approved
password environment variable. PAT automation uses only environment-variable
references in YAML:

```yaml
provider:
  cloud: snowflake
  host_env: SNOWFLAKE_HOST
  user_env: SNOWFLAKE_USERNAME
  token_env: SNOWFLAKE_TOKEN
  auth_type: programmatic_access_token
  warehouse: COMPUTE_WH
  role: SYSADMIN
  execution_mode: live-readonly
```

Validate the source before generating a draft:

```powershell
datamuru validate --config datamuru.yml --strict
datamuru doctor --config datamuru.yml
datamuru import discover --config datamuru.yml --catalog FINANCE
```

## Generate a bounded mapping

```powershell
datamuru import map-databricks `
  --config datamuru.yml `
  --database FINANCE `
  --target-workspace databricks-dev `
  --target-cloud azure `
  --catalog-prefix sf `
  --identifier-case lower `
  --out migrations/snowflake-to-databricks/finance.mapping.yml
```

Repeat `--database` to include more than one database. Omit it only when the
operator intends to review every non-system database returned by discovery.

The draft has this shape:

```yaml
migration:
  source:
    provider: snowflake
  target:
    provider: databricks
    workspace: databricks-dev
    cloud: azure
  naming:
    catalog_prefix: sf
    identifier_case: lower
  mappings:
    databases:
      FINANCE:
        catalog: sf_finance
        schemas:
          RAW: raw
  review:
    status: draft
```

## Naming safeguards

`--identifier-case lower` is the default. Use `preserve` when the review must
retain source casing. Characters outside letters, numbers, and underscores are
normalized to underscores.

DataMuru blocks the draft when two source names normalize to the same target.
For example, `FINANCE-RAW` and `FINANCE_RAW` both normalize to `finance_raw`.
Change the source scope, naming mode, or catalog prefix instead of accepting an
automatic suffix.

## Review boundary

Review:

- database-to-catalog names;
- schema names and collisions;
- target workspace and cloud;
- object ownership and Unity Catalog storage requirements;
- data movement and validation ownership outside DataMuru;
- role and grant redesign between Snowflake and Databricks.

The current draft does not include tables, views, functions, roles, users,
grants, masking policies, row-access policies, pipelines, or data. Those
capabilities remain outside this bounded mapping workflow.

For the opposite direction, see
[Databricks to Snowflake adoption path](databricks-to-snowflake.md).
