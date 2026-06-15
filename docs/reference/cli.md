# CLI reference

```text
datamuru [OPTIONS] COMMAND [ARGS]...
```

## `init`

Create a starter project.

```text
datamuru init
  [--name TEXT]
  [--provider TEXT]
  [--cloud TEXT]
  [--edition TEXT]
  [--output-dir TEXT]
```

Defaults: name `datamuru-project`, provider `databricks`, cloud `azure`,
edition `open-source`, and current output directory.

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
  [--include-system]
  [--output text|json]
```

Requires one workspace declaration and a live execution mode.

## `import generate`

```text
datamuru import generate
  [--config TEXT]
  [--catalog TEXT]...
  [--include-groups]
  [--include-system]
  [--out TEXT]
  [--output text|json]
```

Repeat `--catalog` to select more than one catalog.

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
