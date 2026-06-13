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

## State is not a backup

State does not contain the data stored in a catalog or schema. Back up state,
but also use provider-native data, metadata, and disaster-recovery controls.

## Protect state

- Do not hand-edit fingerprints.
- Do not commit environment state.
- Use one state path per independently operated environment.
- Back up state before adoption or destructive tests.
- Avoid concurrent apply operations against the same state file.
