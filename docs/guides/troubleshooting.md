# Troubleshoot DataMuru

Start with the structured error code and the command that failed.

## Collect safe diagnostics

```powershell
datamuru validate --config datamuru.yml
datamuru doctor --config datamuru.yml --output json
datamuru plan --config datamuru.yml --output json
```

Remove tokens, workspace identifiers, emails, account IDs, and customer names
before sharing output.

## Configuration validation fails

**Symptoms:** `DMR-CFG-1001` or `DMR-CFG-1002`.

**Check:**

- YAML indentation and duplicate keys;
- paths relative to `datamuru.yml`;
- `default_environment` matches an environment name;
- principals are nested under `workspace`;
- Enterprise-only features are disabled in OSS.

## Doctor cannot connect

**Check:**

- the host is the workspace origin;
- `DATABRICKS_TOKEN` is set in the same process;
- the token is active;
- a proxy or firewall is not replacing the response;
- the execution mode is a live mode.

## Catalog creation requires storage

If the REST API reports that the metastore storage root does not exist, choose
one approach:

- set `use_default_storage: true` and configure a SQL warehouse ID;
- provide `managed_location` and ensure Databricks can access it.

## SQL statement request times out

DataMuru may submit a statement and then poll it. Network timeouts do not prove
that Databricks cancelled the operation. Check the workspace before retrying,
then re-plan. Idempotent create operations should observe an object that
completed after the client timed out.

## Schemas fail after catalog failure

Fix the catalog error first. DataMuru skips child schemas when the parent fails
to avoid noisy, misleading API errors.

## Plan says zero changes but target is wrong

Confirm the exact address in [Resource types and addresses](../reference/resources.md).
A target that matches no declaration or state should be reported explicitly.

## Plan repeatedly shows update

Possible causes:

- state was deleted or edited;
- live observation cannot read the object;
- a privilege or attribute differs;
- configuration was generated with unstable or environment-specific values.

Compare JSON plan output, local state, and live Databricks configuration.

## PyPI or CLI command is not found

```powershell
python -m pip show datamuru
python -m pip install --upgrade datamuru
python -m datamuru.cli.main --help
```

If module execution works but `datamuru` does not, reactivate the virtual
environment or fix the environment's scripts path.
