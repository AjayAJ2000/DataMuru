# State and reconciliation

State maps a resource address to a fingerprint and attributes. The fingerprint
represents the desired resource definition.

## Why state exists

State allows DataMuru to:

- recognize previously applied local-only resources;
- detect removed declarations;
- compare desired definitions across runs;
- support deterministic no-op plans.

In live modes, DataMuru observes supported desired resources from Databricks and
uses those observations during planning. Observation is intentionally scoped;
DataMuru does not import every object into state automatically.

## Adoption establishes ownership

`datamuru import adopt` records an existing, declared live resource in the
configured state backend without mutating the provider. Adoption requires an
explicit target and exact agreement between the live and desired fingerprints.
The operation is atomic: conflicts or missing resources prevent all selected
state writes.

## State is not a backup

State does not contain the data stored in a catalog or schema. Back up state,
but also use provider-native data, metadata, and disaster-recovery controls.

## Inspect backend readiness

Use `datamuru state inspect` before plan, apply, adoption, or destructive test
flows when a project may move between local and hosted execution.

Local state reports a ready, read-write backend. Remote backend values such as
`s3`, `azure_blob`, and `gcs` are recognized as shared-state contracts, but the
OSS alpha does not read from or write to those services. The command exits
nonzero for remote backends and returns a structured JSON report so CI and
hosted-control-plane handoffs can fail before mutating anything.

Plan, apply, destroy, and adoption workflows also stop before provider work when
a recognized remote state contract is configured. The runtime raises
`DMR-STATE-REMOTE` with the same backend mode and readiness context reported by
`state inspect`. Use local state for OSS execution or route the project through
a hosted control plane or Enterprise state extension.

## Protect state

- Do not hand-edit fingerprints.
- Do not commit environment state.
- Use one state path per independently operated environment.
- Back up state before adoption or destructive tests.
- Avoid concurrent apply operations against the same state file.
