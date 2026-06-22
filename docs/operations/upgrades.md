# Upgrades and compatibility

DataMuru follows semantic-versioning intent, but `0.x` releases can contain
breaking changes.

## Before upgrading

1. Read the changelog and release notes.
2. Pin the target version in a clean environment.
3. Back up configuration and state.
4. Run validation, doctor, and plan without apply.
5. Compare JSON output used by automation.
6. Test a non-production workspace.

## Install a specific version

```powershell
pip install --upgrade datamuru==0.4.0a0
```

## Verify

```powershell
python -m pip show datamuru
datamuru validate --strict
datamuru doctor
datamuru plan
```

Never downgrade and reuse state without checking whether the older version can
read the current state contract.
