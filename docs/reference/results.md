# Plan and apply results

## Plan

A plan contains:

- `environment`;
- an ordered list of changes;
- each change's `action`, `resource`, `before`, `after`, and `reason`.

Actions are `create`, `update`, `noop`, and `destroy`.

## Saved plan

A saved plan contains:

- `metadata.schema_version`;
- `metadata.created_at`;
- `metadata.project_name` and `metadata.project_version`;
- `metadata.environment`;
- `metadata.provider` and `metadata.provider_cloud`;
- `metadata.config_fingerprint`;
- optional `metadata.target`;
- `plan`, which contains the same plan shape returned by `datamuru plan`.

DataMuru refuses to apply a saved plan when the current project, provider,
environment, or configuration fingerprint no longer matches the reviewed
artifact.

## Apply

An apply result separates:

- successfully applied changes;
- resources that already matched;
- failures with resource addresses, reason text, optional error code, title,
  context, and suggestion.

Apply is not globally transactional. Successful parent-independent resources
may remain applied when another resource fails.

Structured apply failures preserve provider and core error metadata so
automation can group failures by code without parsing formatted terminal text.
Dependency skips use `DMR-APPLY-1001`.

## JSON output

Use `--output json` where supported for diagnostics and automation. Treat output
contracts as alpha APIs: pin the package version and test parsers during
upgrades.
