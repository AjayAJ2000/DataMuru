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

These are currently compiled into internal mask resources so the rest of the
framework can reason about them consistently.

## Supported now

- validate taxonomy and masking YAML shape;
- compile taxonomy and mask declarations into deterministic local resources;
- include those resources in plan output for review.

## Planned

- column-level policy binding;
- provider-backed Databricks column mask installation;
- richer classification-to-policy mapping;
- Enterprise approval workflows for policy rollout.

## Not supported today

- live Databricks column-mask creation;
- object-level grants attached to individual tables, views, volumes, or
  columns;
- automatic discovery of all masking policies from a workspace.

## Current boundary

Taxonomy and masking definitions are validated and compiled into deterministic
resources. The OSS alpha does not install live Databricks column masks. Treat
these files as versioned governance intent until provider-backed enforcement is
implemented.

See [Current capabilities and limits](../reference/capabilities-limits.md) for
canonical status terms.
