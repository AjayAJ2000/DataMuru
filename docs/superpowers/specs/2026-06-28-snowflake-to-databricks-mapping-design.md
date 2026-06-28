# Snowflake To Databricks Mapping Draft Design

Status: implemented, pending milestone release

## Context

DataMuru can discover Snowflake databases and schemas in `live-readonly` mode
and can generate Databricks-to-Snowflake mapping drafts. Live validation on
2026-06-28 confirmed both providers are reachable with redacted credentials:
Databricks discovery returned five catalogs and fifteen schemas, while
Snowflake discovery returned one database and two schemas. The existing
forward mapping generated five valid database drafts.

The reverse direction is absent. `datamuru import map-databricks` currently
returns an unknown-command error, so teams evaluating movement from Snowflake
to Databricks cannot generate the equivalent review contract.

## Goals

- Add a Snowflake-to-Databricks mapping draft command and Python API.
- Map Snowflake databases to Databricks catalogs and Snowflake schemas to
  Databricks schemas.
- Use existing Snowflake `live-readonly` discovery without enabling mutation.
- Support bounded source selection by repeated database options.
- Normalize target identifiers deterministically and detect collisions before
  producing a misleading draft.
- Keep generated output review-only and free of provider credentials.
- Test the implementation with unit tests and the configured live Snowflake
  and Databricks environments.
- Document exact operator tests in the milestone 0.5 runbook.

## Non-goals

- No data copying, SQL translation, table migration, or pipeline migration.
- No Databricks live apply from the mapping command.
- No Snowflake or Databricks mutation.
- No Snowflake role, user, grant, masking policy, or object-level mapping.
- No generic bidirectional mapping framework in this slice.
- No automatic resolution of naming collisions.
- No credential values, raw connector errors, or live inventory names in
  committed test evidence.

## Command Surface

The new command mirrors `import map-snowflake`:

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

Options:

| Option | Behavior |
| --- | --- |
| `--database` | Repeatable Snowflake database selection. Omission maps all discovered non-system databases. |
| `--target-workspace` | Review label for the intended Databricks workspace. |
| `--target-cloud` | Target cloud metadata: `azure`, `aws`, or `gcp`. |
| `--catalog-prefix` | Optional prefix applied before identifier normalization. |
| `--identifier-case` | `lower` by default, with `preserve` also supported. |
| `--out` | Optional mapping YAML destination. |
| `--output` | Existing `text` or `json` output convention. |

The command requires a Snowflake source provider. Running it from a Databricks
project returns a structured validation error before mapping generation.

## Mapping Contract

The generated YAML is explicit and review-first:

```yaml
migration:
  name: snowflake-live-to-databricks-dev
  source:
    provider: snowflake
    workspace: snowflake-live
    environment: dev
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
          CURATED: curated
  review:
    status: draft
    notes:
      - Review catalog and schema names before implementation.
      - This draft does not move data or apply Databricks changes.
```

The result model is `SnowflakeToDatabricksMappingResult` with provider,
environment, source workspace, target workspace, mapping text, selected
databases, and mapped catalogs. It follows the existing
`DatabricksToSnowflakeMappingResult` serialization pattern.

## Identifier Rules

Target catalog and schema identifiers are derived deterministically:

1. apply `catalog_prefix` to database names only;
2. replace non-alphanumeric and non-underscore characters with `_`;
3. collapse repeated underscores and trim leading or trailing underscores;
4. apply the requested case mode;
5. reject an empty normalized identifier;
6. reject duplicate target catalog names or duplicate schema names within one
   catalog.

The engine never chooses a suffix automatically. A collision returns a
`ValidationError` that identifies the conflicting source addresses and target
identifier so the operator can change the prefix or scope deliberately.

## Components And Data Flow

1. `SnowflakeProvider.discover_importable_resources()` returns the existing
   provider-neutral database/schema report.
2. `ImportEngine.snowflake_to_databricks_mapping()` validates source provider,
   requested databases, cloud, naming mode, and collisions.
3. The core engine and `DataMuru` API expose
   `import_snowflake_to_databricks_mapping()`.
4. The CLI writes YAML only when mapping validation succeeds.
5. JSON output returns the structured result and optional resolved output path.

No state backend, provider mutation method, or apply engine participates in
this flow.

## Error Handling

Use existing structured `ValidationError` behavior for:

- unsupported identifier case or target cloud;
- non-Snowflake source provider;
- requested databases absent from discovery;
- empty normalized identifiers;
- target catalog collisions;
- target schema collisions.

Live connector failures remain inside the existing redacted Snowflake provider
boundary. A failed command does not create or partially write the output file.

## Test Strategy

Use failing-first tests for:

1. a bounded Snowflake database/schema mapping draft;
2. default lowercase normalization and optional preservation;
3. catalog prefix handling;
4. missing requested databases;
5. wrong source provider;
6. unsupported cloud and identifier modes;
7. catalog and schema collision blocking;
8. CLI text, JSON, help, and output-file behavior;
9. Python API delegation and result serialization;
10. live Snowflake discovery to Databricks draft generation with aggregate-only
    evidence;
11. no provider mutation and no credential disclosure;
12. full Ruff, pytest, strict MkDocs, and diff checks.

The live test validates the resulting target provider, draft status, mapped
database count, and mapped catalog count. It does not print source or target
inventory names.

## Documentation And Project Tracking

Update:

- CLI and Python API references;
- capability limits as a draft-generation capability;
- a Snowflake-to-Databricks operator guide;
- the milestone 0.5 test runbook;
- roadmap and GitHub Project board source documents;
- changelog.

Create a private project item in `In progress` before implementation. After the
implementation is committed and pushed, attach commit evidence, move the item
through `Validate`, and mark it `Done` only after CI, Documentation, and
Documentation Links all succeed.

## Acceptance Criteria

- `datamuru import map-databricks` exists and requires a Snowflake source.
- Repeated `--database` options bound discovery and mapping scope.
- Generated contracts map databases to catalogs and schemas to schemas.
- Naming is deterministic and collisions stop generation.
- Mapping output is explicitly marked draft and performs no mutation.
- Python and CLI surfaces return structured results.
- Existing Databricks-to-Snowflake behavior remains unchanged.
- The milestone runbook tests both mapping directions feature by feature.
- Live validation passes against the configured provider accounts without
  exposing credentials or inventory names.
- Local gates and all three required GitHub workflows pass.
