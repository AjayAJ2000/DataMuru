# Learn with a local project

This tutorial teaches DataMuru's configuration, planning, state, and
idempotency model without contacting a cloud service.

## Prerequisites

- DataMuru `0.4.0a0` installed
- an empty working directory

## Create the project

```powershell
datamuru init --name local-lab --provider databricks --cloud azure --output-dir .
```

Confirm that `providers/databricks.yml` contains:

```yaml
provider:
  cloud: azure
  execution_mode: state-only
  host_env: DATABRICKS_HOST
  auth_type: pat
  token_env: DATABRICKS_TOKEN
```

This local tutorial does not read `DATABRICKS_HOST` or `DATABRICKS_TOKEN`
because `execution_mode` is `state-only`. The environment-variable shape keeps
the file ready for later `live-readonly` testing without storing workspace
details in YAML.

The host and token are not used in `state-only` mode.

## Declare a catalog

Create or update a file in `workspaces/`:

```yaml
workspace:
  name: local-lab
  cloud: azure
  region: eastus2
  catalogs:
    - name: local_analytics
      schemas:
        - raw
        - curated
```

## Validate and plan

```powershell
datamuru validate --config datamuru.yml --strict
datamuru plan --config datamuru.yml
```

The first plan should contain create actions for the workspace, catalog, and
schemas.

## Apply and inspect state

```powershell
datamuru apply --config datamuru.yml --auto-approve
Get-Content .\.datamuru\state-dev.json
```

The state file contains resource addresses, fingerprints, and attributes. It
does not contain a Databricks token.

## Make a change

Add a `gold` schema:

```yaml
schemas:
  - raw
  - curated
  - gold
```

Run:

```powershell
datamuru plan --config datamuru.yml
```

The plan should create `schema:local_analytics.gold` and leave existing
resources unchanged.

## Verify idempotency

Apply and plan again:

```powershell
datamuru apply --config datamuru.yml --auto-approve
datamuru plan --config datamuru.yml
```

An idempotent plan reports no required changes.

## Clean up

This tutorial created only local files. Delete the directory when finished, or
run targeted destroy before removing it:

```powershell
datamuru destroy --config datamuru.yml --target catalog:local_analytics --confirm-destroy
```

Targeting a catalog also targets its declared schemas.
