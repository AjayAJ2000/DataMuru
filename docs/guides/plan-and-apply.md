# Review and apply changes

## Create a plan

```powershell
datamuru plan --config datamuru.yml
```

Plan actions:

| Symbol | Action | Meaning |
| --- | --- | --- |
| `+` | create | desired resource is not in observed or local state |
| `~` | update | resource fingerprint differs |
| `=` | no-op | desired and current fingerprints match |
| `-` | destroy | state contains a resource no longer declared |

## Review the plan

Before applying, verify:

- the environment and workspace;
- each resource address;
- every destroy action;
- whether the provider mode is `state-only` or `live-apply`;
- that unrelated resources are not included.

## Apply interactively

```powershell
datamuru apply --config datamuru.yml
```

For automation or a reviewed narrow target:

```powershell
datamuru apply --config datamuru.yml --target catalog:analytics --auto-approve
```

## Re-plan

```powershell
datamuru plan --config datamuru.yml --target catalog:analytics
```

A stable configuration should produce no required changes. If it repeatedly
shows updates, inspect live observation, state, and generated attributes.

## Handle partial failure

DataMuru records successful resources and reports failures separately. Child
schemas are skipped when their parent catalog fails. Fix the parent error and
re-plan instead of assuming the whole apply rolled back.
