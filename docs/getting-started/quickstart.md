# Quickstart

This quickstart walks through the current alpha experience using the repo scaffold.

## 1. Validate the root configuration

```bash
python -m datamuru.cli.main validate --config datamuru.yml
```

Expected outcome:

- Configuration files load successfully
- Required root sections are present
- Workspace and governance starter files pass alpha validation

## 2. Inspect the plan

```bash
python -m datamuru.cli.main plan --config datamuru.yml
```

Expected outcome:

- A list of `create` operations for workspace, catalog, schema, governance, and access-control resources

## 3. Apply the local desired state

```bash
python -m datamuru.cli.main apply --config datamuru.yml --auto-approve
```

Expected outcome:

- The local state file is created under `.datamuru/`
- Declared resources are recorded in state

## 4. Re-run the plan

```bash
python -m datamuru.cli.main plan --config datamuru.yml
```

Expected outcome:

- The plan becomes idempotent
- Existing resources show as `noop`

## 5. Destroy the local state

```bash
python -m datamuru.cli.main destroy --config datamuru.yml --confirm-destroy
```

Expected outcome:

- Managed resources are removed from local state
- The project returns to a clean declared-state baseline
