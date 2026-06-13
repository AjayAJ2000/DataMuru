# CLI Reference

The current CLI is intentionally small and focused, but it is now organized as thin command modules over the shared Python API.

## CLI design goals

- thin command handlers
- structured error rendering
- machine-friendly JSON output where relevant
- human-friendly review output for plans and diagnostics

## `datamuru init`

Creates a bootstrap project structure.

Key options:

- `--name`
- `--provider`
- `--cloud`
- `--edition`
- `--output-dir`

## `datamuru validate`

Validates the configuration tree for the selected root config.

Key options:

- `--config`
- `--strict`

## `datamuru plan`

Computes desired-state changes for the current configuration.

Key options:

- `--config`
- `--target`
- `--out`
- `--output {text,json}`

## `datamuru apply`

Applies the current plan through the active provider abstraction and records successful resources in DataMuru state.

Key options:

- `--config`
- `--target`
- `--plan`
- `--auto-approve`

Current note:

- saved-plan apply is supported through `--plan`

## `datamuru destroy`

Destroys managed resources from local state.

Key options:

- `--config`
- `--target`
- `--confirm-destroy`

## `datamuru edition show`

Inspects the active edition and reports enabled and restricted feature sets.

Key options:

- `--config`
- `--output {text,json}`

## `datamuru doctor`

Runs provider-aware setup checks intended to help operators validate local configuration before trying a workflow.

Key options:

- `--config`
- `--output {text,json}`

Current note:

- live ACL discovery and grant application require a Databricks SQL warehouse ID when RBAC permission bindings are declared

## `datamuru import discover`

Discovers brownfield resources from the live provider and prints a reviewable inventory.

Key options:

- `--config`
- `--include-system`
- `--output {text,json}`

Current note:

- the alpha import flow expects exactly one workspace declaration in scope

## `datamuru import generate`

Generates a `workspace:` YAML fragment from live provider discovery so teams can onboard existing objects intentionally.

Key options:

- `--config`
- `--catalog`
- `--include-groups`
- `--include-system`
- `--out`

## Usage guidance

Recommended day-to-day sequence:

1. `datamuru validate`
2. `datamuru doctor`
3. `datamuru plan`
4. `datamuru apply --auto-approve`

For shared environments, save the plan first and treat it as a review artifact.

For live Databricks RBAC work, use a narrower loop:

1. `datamuru validate`
2. `datamuru doctor`
3. `datamuru plan --target permission_binding:<principal>:<role>`
4. `datamuru apply --target permission_binding:<principal>:<role> --auto-approve`
