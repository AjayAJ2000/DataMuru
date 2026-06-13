# Safety model

DataMuru uses layered controls rather than one global safety switch.

## Configuration controls

- edition-aware feature validation;
- explicit identity lifecycle;
- explicit state paths;
- required confirmation flags for destroy.

## Execution controls

- `state-only` avoids provider contact;
- `live-readonly` blocks mutation;
- `live-apply` limits mutation to implemented resource types.

## Review controls

- deterministic plans;
- resource targets;
- saved plans;
- JSON output for automation;
- idempotent re-planning.

## Provider controls

- child schemas are skipped after parent catalog failure;
- system schemas and groups are filtered or protected;
- identity deletion requires `allow_delete: true`;
- unsupported live resources fail instead of silently succeeding.

These controls reduce risk but cannot determine business impact. Operators
remain responsible for authorization, data dependencies, backups, and change
approval.
