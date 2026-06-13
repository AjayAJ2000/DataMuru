# Databricks Free Edition Setup

This guide is the fastest way to try the current DataMuru alpha against your own Databricks personal workspace.

## Current stage

DataMuru is currently in the `v0.1 alpha bootstrap` stage, but the Databricks provider is now a little more real than the original scaffold.

That means:

- the framework shape is real
- the CLI and config model are usable locally
- the provider can now perform a safe read-only workspace connectivity probe
- the planner can now observe some existing workspace resources in live-readonly mode
- the first live Databricks mutation path exists for Unity Catalog catalogs and schemas

So today, you can use Databricks Free Edition to understand the intended workspace and governance model, validate credentials, and verify workspace connectivity while we continue filling in live provider execution.

## What Databricks Free Edition is

According to Databricks' current official docs, Free Edition is the no-cost personal offering that replaced the legacy Community Edition in 2025, and it provides a serverless-only, quota-limited workspace for learning and experimentation. It also has important admin limitations: one workspace and one metastore per account, no account console or account-level APIs, and no private networking or enterprise identity features.

## What this means for DataMuru

For the current alpha:

- Free Edition is good enough to explore the target platform concepts
- Free Edition is useful for validating PAT-based connectivity from DataMuru
- Free Edition is **not** a full substitute for a paid Databricks account if you want to test account-level workspace provisioning later
- some long-term DataMuru features in the PRD will require capabilities not available in Free Edition

### Identity capability

Databricks documents Free Edition as lacking SCIM administration, but DataMuru probes the connected workspace at runtime because capability exposure can vary.

Run `datamuru doctor` and inspect `provider.identity_management`:

- `ok`: the current workspace and credential can use the tested account SCIM endpoint
- `warning` or `error`: use existing principals for ACLs; managed identity mutations are blocked

Managed identity declarations still require DataMuru Enterprise.

## Step 1: create your Databricks Free Edition account

Use the official signup flow:

- Sign up for Databricks Free Edition: [Databricks Free Edition signup guide](https://docs.databricks.com/aws/en/getting-started/free-edition)

If you are evaluating Databricks for commercial or full-platform use instead of personal experimentation, compare it with the free trial:

- Free Edition vs free trial: [Databricks signup options](https://docs.databricks.com/aws/en/getting-started/free-trial-vs-free-edition)

## Step 2: understand the current limitations

Review the official limitations before you try to map PRD expectations to your workspace:

- Official limitations: [Databricks Free Edition limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations)

The most relevant ones for DataMuru today are:

- serverless-only compute
- one workspace and one metastore
- no account-level APIs
- no private networking customization
- no SSO or SCIM

## Step 3: install DataMuru locally

From this repository:

```bash
python -m pip install -e .
```

If you want the optional SDK available in the same environment, install the Databricks extra too:

```bash
python -m pip install -e ".[databricks]"
```

Set your Databricks personal access token in the shell before running the doctor command:

```bash
set DATABRICKS_TOKEN=your_token_here
```

## Step 4: configure provider execution mode

Update `providers/databricks.yml`.

The two important alpha modes are:

- `state-only`
  This is the default. It keeps DataMuru fully local and skips network probing.
- `live-readonly`
  This enables a safe read-only workspace connectivity probe in `doctor`, but still blocks Databricks mutations in `apply`.
- `live-apply`
  This enables the current first live mutation slice. Today that means catalog and schema creation and deletion only.

Recommended Free Edition setup:

```yaml
provider:
  cloud: azure
  credential_mode: personal-access-token
  execution_mode: live-readonly
  auth_type: pat
  token_env: DATABRICKS_TOKEN
  host: https://adb-your-workspace.azuredatabricks.net
```

## Step 5: run doctor, validate, and plan

First, confirm local setup and optional live connectivity:

```bash
python -m datamuru.cli.main doctor --config datamuru.yml
```

Then validate the project:

```bash
python -m datamuru.cli.main validate --config datamuru.yml
python -m datamuru.cli.main plan --config datamuru.yml
```

Current live-read planning coverage:

- workspace presence
- groups
- Unity Catalog catalogs
- Unity Catalog schemas

This means `plan` can now reduce false create actions for those resource types when they already exist in the connected workspace.

## Step 5b: test live catalog and schema creation

If you want to create real objects in Databricks now, switch to:

```yaml
execution_mode: live-apply
```

Then simplify `workspaces/alpha-dev.yml` so it only contains a catalog and schema set you want to test first. A good first example is:

```yaml
workspace:
  name: alpha-dev
  cloud: azure
  region: eastus2
  catalogs:
    - name: alpha_marketing
      schemas:
        - raw
```

If your workspace requires an explicit managed location for catalog creation, use:

```yaml
workspace:
  name: alpha-dev
  cloud: azure
  region: eastus2
  catalogs:
    - name: alpha_marketing
      managed_location: abfss://catalog-root@storageaccount.dfs.core.windows.net/alpha_marketing
      schemas:
        - name: raw
          managed_location: abfss://schema-root@storageaccount.dfs.core.windows.net/alpha_marketing/raw
```

DataMuru maps `managed_location` to the Unity Catalog storage root fields for the live catalog and schema create APIs.

Then run:

```bash
python -m datamuru.cli.main plan --config datamuru.yml --target catalog:alpha_marketing
python -m datamuru.cli.main apply --config datamuru.yml --target catalog:alpha_marketing --auto-approve
```

Why `--target` matters right now:

- live catalog and schema creation is implemented
- groups and service principals are not implemented for live apply yet
- targeting the catalog avoids unrelated unsupported resource types

## Step 6: map your Free Edition workspace to the current config model

Update these files for your local trial:

- `providers/databricks.yml`
- `workspaces/alpha-dev.yml`
- optionally `governance/*.yml`

At a minimum, set:

- your Databricks workspace host URL
- the selected cloud family
- a PAT-backed auth configuration for local trial usage
- the provider execution mode
- workspace naming and starter catalog intent

## Step 7: use the alpha for safe workflow validation

At the current stage, the most realistic trial flow is:

1. sign up for Free Edition
2. inspect your workspace shape in Databricks
3. mirror that shape in the DataMuru config files
4. run `doctor`, `validate`, and `plan`
5. use `apply` only in local `state-only` modeling mode
6. review how DataMuru models your intended environment

## What you cannot fully test yet

Because the provider is still in the alpha execution stage, this repository does not yet:

- provision a real Databricks workspace
- manage account-level resources
- perform live `apply` mutations for every resource type
- observe every PRD resource type from the live workspace

Those gaps are expected at this stage and are the next implementation direction after the connectivity baseline.

## Recommended trial expectation

Treat your first Databricks Free Edition run as:

- a product walkthrough
- a config-model evaluation
- a credential and connectivity validation flow
- a future-operator onboarding test

Do not treat it yet as full end-to-end production provisioning.
