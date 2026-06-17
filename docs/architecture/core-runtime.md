# Core Runtime Layout

The alpha runtime now follows the long-term product structure more closely so the OSS and Enterprise tracks can evolve without collapsing into one monolithic module.

## Core packages

### `datamuru/core/config/`

Owns configuration parsing, interpolation, schema-aware validation, and loaded project resolution.

Main responsibilities:

- load `datamuru.yml`
- resolve environment and provider references
- validate edition-aware feature flags
- build typed in-memory project objects

### `datamuru/core/state/`

Owns state models, backend contracts, and backend resolution.

Current alpha support:

- local JSON state backend

Reserved extension path:

- S3
- Azure Blob
- GCS

### `datamuru/core/plan/`

Owns desired-state comparison and deterministic change generation.

Main responsibilities:

- resource fingerprinting
- target filtering
- create, update, noop, and destroy decisioning

### `datamuru/core/apply/`

Owns execution over an approved plan and persistence back into state.

Main responsibilities:

- execute provider operations
- update state snapshots
- return structured apply outcomes

### `datamuru/core/importer/`

Owns brownfield discovery, YAML generation, and conservative state adoption.

Current alpha behavior:

- discover supported live Databricks resources;
- generate reviewable workspace YAML;
- adopt explicitly targeted matching live resources into local state;
- block adoption when live fingerprints conflict with declared config.

## Why this matters

This structure makes it easier to:

- publish the framework as a PyPI package
- keep CLI commands thin
- test config, plan, state, and provider behavior independently
- add OSS and Enterprise capabilities in parallel without forking the codebase too early
