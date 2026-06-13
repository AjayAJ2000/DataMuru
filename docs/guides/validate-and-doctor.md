# Validate and diagnose setup

`validate` checks the DataMuru configuration. `doctor` checks runtime provider
requirements. Run both before plan or apply.

## Validate configuration

```powershell
datamuru validate --config datamuru.yml
```

Validation detects:

- missing required root keys and referenced files;
- unsupported editions, clouds, and state backends;
- invalid workspace and principal shapes;
- unavailable edition features;
- taxonomy and RBAC structural problems;
- invalid provider authentication configuration.

Use strict mode in CI:

```powershell
datamuru validate --config datamuru.yml --strict
```

## Diagnose the provider

```powershell
datamuru doctor --config datamuru.yml
```

Doctor checks:

- cloud, host, auth mode, and token availability;
- execution mode;
- workspace declarations;
- Databricks connectivity in live modes;
- SQL warehouse requirements for default storage and ACLs;
- identity capability when managed identities are declared.

For automation:

```powershell
datamuru doctor --config datamuru.yml --output json
```

## Interpret levels

- `ok`: the check passed.
- `warning`: the workflow may continue, but review the limitation.
- `error`: fix the problem before a live operation.

Validation success does not prove that Databricks permissions are sufficient.
Doctor success does not prove that every planned mutation is authorized.
