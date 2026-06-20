# CLI reference

```text
datamuru [OPTIONS] COMMAND [ARGS]...
```

By default, interactive commands print the DataMuru branded CLI header. Use
`--no-banner` before the command name when scripting:

```powershell
datamuru --no-banner validate --config datamuru.yml
```

## `init`

Create a starter project.

```text
datamuru init
  [--name TEXT]
  [--provider TEXT]
  [--cloud TEXT]
  [--edition TEXT]
  [--execution-mode state-only|live-readonly|live-apply]
  [--output-dir TEXT]
```

Defaults: name `datamuru-project`, provider `databricks`, cloud `azure`,
edition `open-source`, execution mode `state-only`, and current output
directory.

The generated Databricks provider config uses `host_env`, `token_env`, and
`sql_warehouse_id_env` so workspace-specific values stay outside YAML.

## `validate`

```text
datamuru validate [--config TEXT] [--strict]
```

`--strict` fails when validation returns warnings.

## `doctor`

```text
datamuru doctor [--config TEXT] [--output text|json]
```

Runs provider-aware diagnostics. Default config: `datamuru.yml`.

## `plan`

```text
datamuru plan
  [--config TEXT]
  [--target TEXT]
  [--out TEXT]
  [--output text|json]
```

`--out` writes a saved plan. `--target` accepts a resource address.

## `apply`

```text
datamuru apply
  [--config TEXT]
  [--target TEXT]
  [--plan TEXT]
  [--auto-approve]
```

Use either current configuration planning or `--plan` for a saved plan.

## `destroy`

```text
datamuru destroy
  [--config TEXT]
  [--target TEXT]
  [--confirm-destroy]
```

Destruction requires `--confirm-destroy`.

## `import discover`

```text
datamuru import discover
  [--config TEXT]
  [--catalog TEXT]...
  [--include-system]
  [--include-identities]
  [--include-grants]
  [--grant-scope catalog|schema|all]
  [--max-grant-objects INTEGER]
  [--max-catalog-grant-objects INTEGER]
  [--max-schema-grant-objects INTEGER]
  [--progress-checkpoint TEXT]
  [--job-checkpoint TEXT]
  [--resume-from TEXT]
  [--output text|json]
```

Requires one workspace declaration and a live execution mode. Text output shows
a progress bar with the current provider stage. JSON output suppresses progress
so automation can parse stdout safely.

Repeat `--catalog` to restrict catalog, schema, and grant discovery to selected
catalogs. `--include-grants` defaults to `--grant-scope catalog` so broad
enterprise imports do not accidentally scan every schema grant. Use
`--grant-scope all` only after scoping catalogs and estimating warehouse cost.
`--max-grant-objects` stops the run before expensive grant discovery starts
when too many catalog/schema objects are in scope. Use
`--max-catalog-grant-objects` and `--max-schema-grant-objects` to set separate
caps for each object type. This keeps a workspace with few catalogs but many
schemas from launching an unexpectedly large SQL grant scan.
`--progress-checkpoint` writes the latest structured progress event to JSON so
long-running imports can be observed from another terminal or CI step.
`--job-checkpoint` writes resumable grant-scan state, including completed grant
targets and discovered grants. `--resume-from` loads a previous job checkpoint
and skips completed grant targets while refreshing catalog/schema inventory.

## `import generate`

```text
datamuru import generate
  [--config TEXT]
  [--catalog TEXT]...
  [--include-groups]
  [--include-identities]
  [--include-grants]
  [--grant-scope catalog|schema|all]
  [--max-grant-objects INTEGER]
  [--max-catalog-grant-objects INTEGER]
  [--max-schema-grant-objects INTEGER]
  [--progress-checkpoint TEXT]
  [--job-checkpoint TEXT]
  [--resume-from TEXT]
  [--include-system]
  [--out TEXT]
  [--suite-out TEXT]
  [--suite-layout standard|enterprise]
  [--suite-prefix TEXT]
  [--output text|json]
```

Repeat `--catalog` to select more than one catalog.
Use `--suite-layout enterprise` with `--suite-out` when generated review files
must include provider, environment, workspace, and catalog scope in their file
names. Use `--suite-prefix` only when your organization has a stricter naming
standard.

## `import adopt`

```text
datamuru import adopt
  [--config TEXT]
  --target TEXT...
  [--auto-approve]
  [--output text|json]
```

Preview is the default. Repeat `--target` to select multiple declared
resources. A catalog target also selects its declared schemas.
`--auto-approve` writes state only when every selected resource exists live and
matches its declared fingerprint.

## `edition show`

```text
datamuru edition show [--config TEXT] [--output text|json]
```

Reports the configured edition and enabled or restricted features.

## Exit behavior

Commands return a nonzero exit code for structured DataMuru errors. Do not parse
human-formatted Rich output in automation; use JSON output where available.
