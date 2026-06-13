# Classification and Masking

The current repository includes starter taxonomy and masking configuration under `governance/`.

## Taxonomy model

Taxonomy files define categories such as:

- `internal`
- `confidential`
- `pii_personal`

These categories provide structured metadata for how data should be handled.

## Masking model

The alpha ships starter built-in masking definitions, including:

- `partial_mask`
- `full_mask`

These are currently compiled into internal mask resources so the rest of the framework can reason about them consistently.

## Current boundary

Taxonomy and masking definitions are validated and compiled into deterministic
resources. The OSS alpha does not install live Databricks column masks. Treat
these files as versioned governance intent until provider-backed enforcement is
implemented.
