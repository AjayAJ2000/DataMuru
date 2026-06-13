# Error Model

DataMuru now exposes a structured error contract instead of treating every failure as a raw exception string.

## Base error

All product-facing failures inherit from `DataMuruError`.

Each error can carry:

- `code`
- `title`
- `description`
- `context`
- `suggestion`
- `exit_code`

## Current structured error families

### `ConfigLoadError`

Used when configuration files cannot be found, parsed, or interpreted.

### `ValidationError`

Used when configuration content is structurally or semantically invalid.

### `ProviderError`

Used when provider selection or provider execution cannot proceed safely.

### `SavedPlanError`

Used when a saved plan file is missing or invalid for apply-time execution.

### `StateBackendError`

Used when state loading or backend selection fails.

### `UnsupportedOperationError`

Used for capabilities that are intentionally reserved for later milestones, such as brownfield import in the current alpha.

## CLI behavior

The CLI renders structured DataMuru errors with:

- a stable error code
- a human-readable title
- descriptive context
- an actionable suggestion

This is especially important once the framework is distributed on PyPI and consumed by multiple teams, because consistent error contracts reduce support friction and improve automation reliability.
