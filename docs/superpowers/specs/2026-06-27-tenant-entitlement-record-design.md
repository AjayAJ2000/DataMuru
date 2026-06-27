# Tenant entitlement record design

Status: approved approach, pending written-spec review

## Context

Milestone 0.5 can already produce activation readiness, purchase, evidence,
control-plane, architecture, and aggregate handoff artifacts. The next hosted
control-plane backlog item is `HCP-B1: Tenant and entitlement registry`.

The OSS package must not pretend to provide a hosted registry. This slice
therefore produces one immutable, redacted tenant entitlement record that a
future registry can consume.

## Goals

- Bind organization, tenant, region, control-plane endpoint, support plan, and
  requested entitlements in one versioned JSON contract.
- Produce a stable record identifier for duplicate and change detection.
- Keep the workflow offline and safe to run from an OSS checkout.
- Exclude license keys, provider tokens, and other secret values.
- Expose the same behavior through CLI and Python APIs.
- Include the record in the Enterprise activation handoff package.
- Extend the milestone 0.5 runbook with ready, blocked, redaction, fingerprint,
  and package-integration tests.

## Non-goals

- No hosted tenant provisioning.
- No license issuance or license-server calls.
- No mutable local registry, list, update, or delete commands.
- No remote API client.
- No billing or payment processing.
- No provider or state mutation.
- No remote-state implementation.

## Public CLI

```text
datamuru enterprise control-plane tenant-record
  [--config TEXT]
  --out TEXT
  [--allow-blocked]
  [--output text|json]
```

Default behavior:

- Build the record from the configured Enterprise activation contract.
- Refuse to write a file when activation is blocked.
- Exit nonzero when blocked.
- Print a concise human-readable summary in text mode.
- Print the complete redacted record in JSON mode.

With `--allow-blocked`, write a diagnostic record containing failed activation
checks. This option is intended only for support triage.

## Python API

```python
dm.enterprise_tenant_entitlement_record()
dm.write_enterprise_tenant_entitlement_record(output_path)
```

The engine and public API use the same builder and writer as the CLI.

## Record contract

Schema version:

```text
datamuru.tenant_entitlement_record.v1
```

Top-level fields:

| Field | Purpose |
| --- | --- |
| `schema_version` | Versioned consumer contract. |
| `generated_at` | UTC generation timestamp. |
| `status` | `ready` or `blocked`. |
| `ready` | Machine-readable readiness boolean. |
| `record_id` | Stable identifier derived from canonical redacted content. |
| `project` | DataMuru project name, provider, and default environment. |
| `tenant` | Organization, tenant ID, region, and control-plane URL. |
| `entitlement` | Support plan, purchase reference, enabled features, and license-presence metadata. |
| `source` | Activation schema version and stable content fingerprint metadata. |
| `checks` | Redacted activation checks. |
| `security` | Offline and non-mutation guarantees. |

## Stable identity

`record_id` is calculated from a canonical JSON encoding of stable redacted
fields. The input excludes `generated_at`, local absolute paths, and secret
values. It also excludes readiness status, checks, and `license_key_present`
because those values describe runtime posture rather than tenant identity.
Rebuilding an unchanged tenant and entitlement binding must produce the same
identifier even when license-key availability changes.

The identifier format is:

```text
ter_<first 20 hexadecimal characters of SHA-256>
```

Changing a bound tenant or entitlement field must change the identifier.

## Entitlement mapping

The record includes enabled Enterprise features from the activation payload:

- `hosted_control_plane`;
- `identity_management`;
- `multi_workspace`;
- `compliance_reporting`.

It records `license_key_env` and `license_key_present`, but never records the
license key value.

## Security contract

Every record includes:

```json
{
  "offline": true,
  "provisions_tenant": false,
  "calls_license_server": false,
  "mutates_provider": false,
  "mutates_state": false,
  "secret_values_included": false
}
```

The record must not include absolute local project paths. This keeps the
artifact suitable for reviewed onboarding and support handoff.

## Handoff package integration

`datamuru enterprise activation package` adds:

```text
tenant-entitlement-record.json
```

The package manifest artifact count increases from five to six. The manifest
records the new artifact schema version, status, and readiness.

Blocked package behavior remains unchanged: without `--allow-blocked`, no
package directory is written. A diagnostic package includes a blocked tenant
record when explicitly allowed.

## Internal structure

Add `datamuru/enterprise/registry.py` containing:

- `TenantEntitlementRecord`;
- `build_tenant_entitlement_record()`;
- `write_tenant_entitlement_record()`;
- canonical payload and stable identifier helpers.

Reuse `build_activation_report()` for readiness and redacted activation data.
Do not duplicate activation validation rules.

Update:

- `datamuru.enterprise` exports;
- `DataMuruEngine`;
- `DataMuru` Python API;
- enterprise CLI commands;
- activation handoff package generation;
- CLI, Python API, activation guide, capability, roadmap, changelog, and
  milestone runbook documentation.

## Error handling

- Missing or invalid Enterprise activation fields are represented by existing
  activation checks.
- The CLI exits nonzero and writes no file when blocked by default.
- `--allow-blocked` writes a diagnostic record with checks and redaction
  guarantees.
- File-system errors use the existing CLI error guard.
- No network errors are possible because the feature is offline.

## Test strategy

Use test-first development.

1. Builder returns a ready, redacted record for valid Enterprise activation.
2. Builder returns a blocked record with activation checks for OSS config.
3. Stable inputs produce the same `record_id` across generation timestamps.
4. License-key availability changes do not change `record_id`.
5. Tenant or entitlement changes produce a different `record_id`.
6. Secret values and absolute local paths are absent from serialized output.
7. CLI writes a ready record and emits valid JSON.
8. CLI blocks without creating a file by default.
9. CLI writes a blocked diagnostic record only with `--allow-blocked`.
10. Python API builder and writer expose the same contract.
11. Activation package includes the sixth artifact and updates its manifest.
12. Full unit, lint, documentation, and strict MkDocs gates pass.

## Documentation and runbook

Add a milestone 0.5 runbook section with:

- ready export command;
- expected field and schema checks;
- deterministic fingerprint rerun check;
- secret and local-path redaction checks;
- blocked default behavior;
- `--allow-blocked` diagnostic behavior;
- activation package integration checks;
- bug evidence checklist.

## Acceptance criteria

- The record implements the documented v1 schema.
- Stable identity behavior is covered by failing-first tests.
- No secret values or absolute local paths are serialized.
- CLI and Python APIs produce equivalent records.
- The activation package includes exactly six listed artifacts.
- Existing activation, evidence, control-plane, and package behavior remains
  compatible except for the intentional manifest artifact-count increase.
- Documentation and the milestone 0.5 runbook match the implementation.
- CI, Ruff, pytest, docs tests, and strict MkDocs build pass.
