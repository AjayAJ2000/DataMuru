# Databricks to Snowflake adoption path

DataMuru is provider-agnostic by design. Databricks is the first live apply
provider, and Snowflake now supports live-readonly database/schema discovery.
That means teams can model Snowflake targets, inspect Snowflake trial inventory,
test naming and governance contracts, and prepare for live Snowflake execution
as the provider matures.

This guide explains the practical enterprise path for moving from Databricks
inventory to Snowflake declarations.

## Target outcome

An enterprise should be able to:

1. Import a bounded Databricks workspace or catalog.
2. Generate reviewable DataMuru YAML.
3. Map Databricks catalogs and schemas to Snowflake databases and schemas.
4. Review RBAC and governance differences.
5. Plan Snowflake target state before any live Snowflake apply.
6. Promote to live execution only after credentials, warehouse, role, and safety
   controls are approved.

## Free Snowflake trial setup

Use a Snowflake trial account for local validation. Create or identify:

- account identifier;
- user or SSO login;
- warehouse for tests;
- role with access to inspect the test database and schemas.

Configure environment variables:

```powershell
$env:SNOWFLAKE_ACCOUNT="your-organization-your-account"
$env:SNOWFLAKE_USER="your-user"
```

The account value is the Snowflake organization-account identifier, not the
full browser hostname. Browser SSO is the default. For a disposable trial user
used by automation, set `SNOWFLAKE_PASSWORD` in the shell and change the
provider to `auth_type: snowflake` with
`password_env: SNOWFLAKE_PASSWORD`.

Use a provider file:

```yaml
provider:
  cloud: snowflake
  account_env: SNOWFLAKE_ACCOUNT
  user_env: SNOWFLAKE_USER
  auth_type: externalbrowser
  warehouse: COMPUTE_WH
  role: SYSADMIN
  execution_mode: live-readonly
```

`live-readonly` is intentional for the current OSS release. It lets teams inspect
Snowflake databases and schemas without mutating Snowflake.

## Mapping model

DataMuru uses provider-neutral resource concepts.

| DataMuru concept | Databricks | Snowflake |
| --- | --- | --- |
| Catalog | Unity Catalog catalog | Database |
| Schema | Schema | Schema |
| Group | Workspace/account group | Role or user group pattern |
| Permission binding | Unity Catalog grant | Grant on database/schema/object |
| Taxonomy | Governance classification | Governance classification |

The first migration contract should be explicit:

```yaml
migration:
  name: us-poc-dev-to-snowflake-dev
  source:
    provider: databricks
    workspace: us-poc-dev
  target:
    provider: snowflake
    account: analytics-dev
  mappings:
    catalogs:
      finance_raw:
        database: FINANCE_RAW
        schemas:
          raw: RAW
          silver: SILVER
          gold: GOLD
```

## Practical workflow

Run a bounded Databricks discovery:

```powershell
datamuru import discover --config datamuru.yml --catalog finance_raw
```

Generate a review suite:

```powershell
datamuru import generate --config datamuru.yml --catalog finance_raw --include-identities --include-grants --grant-scope catalog --suite-out imports/databricks
```

Draft the Snowflake mapping contract from the same bounded Databricks scope:

```powershell
datamuru import map-snowflake `
  --config datamuru.yml `
  --catalog finance_raw `
  --target-account analytics-dev `
  --target-workspace snowflake-dev `
  --database-prefix DM `
  --out migrations/databricks-to-snowflake/finance-raw.mapping.yml
```

The mapping draft is intentionally review-first. It does not move data, create
Snowflake databases, or apply grants. Review:

- catalog-to-database names;
- schema casing and reserved-word risk;
- RBAC and role-model differences;
- data movement ownership;
- whether each source catalog should become one Snowflake database or be split.

Create a Snowflake target project or switch the provider config:

```powershell
datamuru init --name dm-snowflake-trial --edition enterprise --provider snowflake --execution-mode state-only --output-dir .\snowflake-trial
```

Switch the Snowflake provider to `live-readonly` when you want to inspect an
existing trial account:

```powershell
datamuru import discover --config .\snowflake-trial\datamuru.yml --catalog FINANCE
```

Review the target plan:

```powershell
datamuru validate --config .\snowflake-trial\datamuru.yml --strict
datamuru plan --config .\snowflake-trial\datamuru.yml
```

## Current limitation

Snowflake live apply, destroy, identity import, and grant import are not enabled
in the current OSS release. That is deliberate. The provider needs tested SQL
mutation behavior, idempotent grants, and destroy safety before it should mutate
enterprise accounts.

## Enterprise next step

The Enterprise version should add:

- database and schema apply;
- role, user, and grant import;
- assisted Databricks-to-Snowflake mapping review and approval workflows;
- migration review experience after CLI-first workflows are stable;
- resumable import jobs for large accounts;
- evidence export for security and change review.
