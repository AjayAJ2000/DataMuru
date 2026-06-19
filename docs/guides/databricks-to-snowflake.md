# Databricks to Snowflake adoption path

DataMuru is provider-agnostic by design. Databricks is the first live provider,
and Snowflake is currently available as a state-only provider scaffold. That
means teams can model Snowflake targets today, test naming and governance
contracts, and prepare for live Snowflake execution as the provider matures.

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
- role with permission to create databases and schemas in the test account.

Configure environment variables:

```powershell
$env:SNOWFLAKE_ACCOUNT="your-account"
$env:SNOWFLAKE_USER="your-user"
```

Use a provider file:

```yaml
provider:
  cloud: snowflake
  account_env: SNOWFLAKE_ACCOUNT
  user_env: SNOWFLAKE_USER
  auth_type: externalbrowser
  warehouse: COMPUTE_WH
  role: SYSADMIN
  execution_mode: state-only
```

`state-only` is intentional for the current OSS release. It lets teams validate
the target model without mutating Snowflake.

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

Create a Snowflake target project or switch the provider config:

```powershell
datamuru init --name dm-snowflake-trial --edition enterprise --provider snowflake --execution-mode state-only --output-dir .\snowflake-trial
```

Review the target plan:

```powershell
datamuru validate --config .\snowflake-trial\datamuru.yml --strict
datamuru plan --config .\snowflake-trial\datamuru.yml
datamuru ui --config .\snowflake-trial\datamuru.yml --port 8765
```

## Current limitation

Snowflake live discovery and live apply are not enabled in the current OSS
release. That is deliberate. The provider needs tested SQL execution,
authentication handling, idempotent grants, and destroy safety before it should
mutate enterprise accounts.

## Enterprise next step

The Enterprise version should add:

- live Snowflake inventory discovery;
- database and schema apply;
- role, user, and grant import;
- Databricks-to-Snowflake mapping generation;
- migration review UI;
- resumable import jobs for large accounts;
- evidence export for security and change review.
