# Enterprise Rollout Playbook

This playbook describes how a platform team can introduce DataMuru without
turning the first deployment into a large migration project.

## Phase 0: Product fit

Answer these questions before writing production YAML:

- Which team owns DataMuru configuration reviews?
- Which Databricks workspaces are in scope?
- Which resources are safe for the first live test?
- Which identity operations require Enterprise support and account SCIM?
- Where will state and saved-plan artifacts live?
- What is the rollback and cleanup process for test resources?

If the answers are unclear, run a local or sandbox evaluation first. Confirm the
scope against [current capabilities and limits](../reference/capabilities-limits.md)
before treating a workflow as supported.

## Phase 1: Local proof

Run a no-cloud workflow:

```powershell
datamuru init --name platform-proof --output-dir .
datamuru validate --config datamuru.yml --strict
datamuru plan --config datamuru.yml
datamuru apply --config datamuru.yml --auto-approve
datamuru plan --config datamuru.yml
```

Success means the team understands project layout, state behavior, plan output,
and idempotency.

## Phase 2: Read-only workspace proof

Move to `live-readonly`:

```yaml
provider:
  execution_mode: live-readonly
  host_env: DATABRICKS_HOST
  token_env: DATABRICKS_TOKEN
  sql_warehouse_id_env: DATABRICKS_SQL_WAREHOUSE_ID
```

Run:

```powershell
datamuru validate --config datamuru.yml --strict
datamuru doctor --config datamuru.yml
datamuru plan --config datamuru.yml --target catalog:dm_rollout_smoke
```

Success means credentials, workspace access, SQL warehouse visibility, and
provider observation are understood.

## Phase 3: Narrow live apply

Use one unique catalog name:

```yaml
catalogs:
  - name: dm_rollout_smoke_01
    use_default_storage: true
    schemas:
      - raw
      - bronze
      - silver
      - gold
```

Switch to `live-apply` and apply only that catalog:

```powershell
datamuru apply --config datamuru.yml --target catalog:dm_rollout_smoke_01 --auto-approve
datamuru plan --config datamuru.yml --target catalog:dm_rollout_smoke_01
```

Success means DataMuru can safely create and reconcile a live target.

## Phase 4: Governance proof

Test one RBAC assignment for an existing group:

```powershell
datamuru plan --config datamuru.yml --target permission_binding:data-consumers:curated_reader
datamuru apply --config datamuru.yml --target permission_binding:data-consumers:curated_reader --auto-approve
```

Success means the SQL warehouse path, Unity Catalog grant path, and principal
names are working.

## Phase 5: Brownfield review

Use import discovery for an existing non-critical catalog:

```powershell
datamuru import discover --config datamuru.yml --output json
datamuru import generate --config datamuru.yml --catalog existing_catalog --out .\workspaces\existing-review.yml
```

Review generated YAML before adoption. Do not import everything and apply
blindly.

Targeted import/adoption workflows are available where supported. Automatic
broad ownership adoption across a workspace is not available in this alpha.

## Phase 6: Enterprise identity proof

Only test managed identity lifecycle in a sandbox account with account SCIM:

```yaml
project:
  edition: enterprise

features:
  identity_management: true
```

Declare one test group with `allow_delete: false`. Apply and verify membership
behavior before creating service principals or users.

## Operating controls

Every rollout stage should define:

- owner;
- reviewer;
- target workspace;
- target resources;
- execution mode;
- state location;
- saved-plan location;
- cleanup command;
- evidence location.

If a stage cannot name those controls, pause before using `live-apply`.
