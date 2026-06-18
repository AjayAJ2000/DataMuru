# Enterprise Testing Runbook

Use this runbook when validating DataMuru in a full Databricks enterprise
workspace or account. It assumes you are testing non-production resources.

!!! danger "Use a sandbox first"
    `live-apply` can create catalogs, schemas, grants, and Enterprise identity
    resources where the Databricks account supports the required APIs. Do not
    point the first test at production catalogs, production groups, or shared
    administrator identities.

## 1. Prepare access

You need:

- Python 3.10 or newer;
- a Databricks workspace URL;
- a personal access token or supported enterprise authentication path;
- a SQL warehouse ID for default-storage catalog creation and grant inspection;
- Unity Catalog permissions to create the target catalog and schemas;
- account SCIM/admin capability if testing managed users, groups, service
  principals, or group memberships.

For the alpha package, PAT authentication is the quickest smoke-test path.
Enterprise testing should also validate Databricks CLI profile auth or the
approved Enterprise credential extension.

## 2. Install DataMuru

Install the released package:

```powershell
python -m pip install --upgrade datamuru==0.3.0a0
```

For Databricks SDK experiments, install the optional extra:

```powershell
python -m pip install --upgrade "datamuru[databricks]==0.3.0a0"
```

## 3. Create a project

```powershell
mkdir datamuru-enterprise-test
cd datamuru-enterprise-test
datamuru init --name datamuru-enterprise-test --edition enterprise --execution-mode live-readonly --output-dir .
```

The generated provider config uses environment variables:

```yaml
provider:
  cloud: azure
  execution_mode: live-readonly
  host_env: DATABRICKS_HOST
  auth_type: pat
  token_env: DATABRICKS_TOKEN
  sql_warehouse_id_env: DATABRICKS_SQL_WAREHOUSE_ID
```

For an enterprise laptop that already uses Databricks CLI SSO, replace the auth
fields with:

```yaml
provider:
  cloud: azure
  execution_mode: live-readonly
  auth_type: databricks-cli
  profile: enterprise-dev
  sql_warehouse_id_env: DATABRICKS_SQL_WAREHOUSE_ID
```

## 4. Set environment variables

Set values in the same shell that runs DataMuru:

```powershell
$env:DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
$env:DATABRICKS_TOKEN="your-token"
$env:DATABRICKS_SQL_WAREHOUSE_ID="your-sql-warehouse-id"
```

For CLI profile auth:

```powershell
databricks auth login --profile enterprise-dev
$env:DATABRICKS_CONFIG_PROFILE="enterprise-dev"
$env:DATABRICKS_SQL_WAREHOUSE_ID="your-sql-warehouse-id"
```

Do not commit real values to `.env.example`, YAML, state, support tickets, or
screenshots.

## 5. Validate and diagnose

```powershell
datamuru validate --config datamuru.yml --strict
datamuru doctor --config datamuru.yml
```

Expected result:

- validation succeeds;
- doctor reports the workspace host, token environment variable, execution
  mode, SQL warehouse setting, workspace declarations, and connectivity;
- managed identity capability appears only when managed identities are declared.

If `doctor` cannot see an environment variable, set it again in the same
PowerShell window.

## 6. Run a read-only plan

Use a unique catalog name before live apply:

```yaml
workspace:
  name: enterprise-dev
  cloud: azure
  region: eastus2
  catalogs:
    - name: dm_enterprise_smoke_01
      use_default_storage: true
      schemas:
        - raw
        - bronze
        - silver
        - gold
```

Then run:

```powershell
datamuru plan --config datamuru.yml --target catalog:dm_enterprise_smoke_01
```

Review every planned resource before applying.

## 7. Apply catalog and schemas

Change provider execution mode:

```yaml
execution_mode: live-apply
```

Apply only the test target:

```powershell
datamuru apply --config datamuru.yml --target catalog:dm_enterprise_smoke_01 --auto-approve
datamuru plan --config datamuru.yml --target catalog:dm_enterprise_smoke_01
```

Expected result:

- apply reports created resources;
- the follow-up plan reports matching resources or no required create/update
  changes.

## 8. Test RBAC grants

Add an RBAC assignment that targets the test catalog:

```yaml
rbac:
  roles:
    - id: smoke_reader
      name: Smoke Reader
      permissions:
        - resource_type: schema
          resource_pattern: "*.gold"
          privilege: SELECT
  assignments:
    - principal: your-existing-group
      type: group
      roles:
        - smoke_reader
      domains:
        - dm_enterprise_smoke_01
```

Run:

```powershell
datamuru validate --config datamuru.yml --strict
datamuru plan --config datamuru.yml --target permission_binding:your-existing-group:smoke_reader
datamuru apply --config datamuru.yml --target permission_binding:your-existing-group:smoke_reader --auto-approve
datamuru plan --config datamuru.yml --target permission_binding:your-existing-group:smoke_reader
```

## 9. Test managed identities

Enable identity management only in an enterprise sandbox:

```yaml
project:
  edition: enterprise

features:
  identity_management: true
```

Declare a test group:

```yaml
workspace:
  principals:
    groups:
      - name: dm-smoke-consumers
        lifecycle: managed
        allow_delete: false
        members:
          users:
            - your.user@company.com
```

Run:

```powershell
datamuru validate --config datamuru.yml --strict
datamuru doctor --config datamuru.yml
datamuru plan --config datamuru.yml --target group:dm-smoke-consumers
datamuru apply --config datamuru.yml --target group:dm-smoke-consumers --auto-approve
```

If doctor reports missing account SCIM capability, keep testing catalogs,
schemas, and RBAC in OSS-compatible mode and defer managed identity tests to a
workspace/account with account SCIM support.

## 10. Test import and adoption

Keep `live-readonly` for import review:

```powershell
datamuru import discover --config datamuru.yml --output json
datamuru import discover --config datamuru.yml --include-identities --include-grants --output json
datamuru import generate --config datamuru.yml --catalog dm_enterprise_smoke_01 --suite-out .\import-review
datamuru import adopt --config datamuru.yml --target catalog:dm_enterprise_smoke_01
datamuru import adopt --config datamuru.yml --target catalog:dm_enterprise_smoke_01 --auto-approve
```

Adoption writes local state only. It does not mutate Databricks.

## 11. Save and apply a reviewed plan

```powershell
datamuru plan --config datamuru.yml --target catalog:dm_enterprise_smoke_01 --out .\plans\smoke-plan.json
datamuru apply --config datamuru.yml --plan .\plans\smoke-plan.json --auto-approve
```

If YAML changes after the saved plan is created, DataMuru rejects the stale
plan. Generate a fresh plan instead of editing JSON.

## 12. Destroy test resources

Only destroy unique test resources:

```powershell
datamuru destroy --config datamuru.yml --target catalog:dm_enterprise_smoke_01 --confirm-destroy
```

Re-run plan afterward and verify no unmanaged production resources are included.

## 13. Capture evidence

For each enterprise test run, save:

- package version;
- sanitized `validate` output;
- sanitized `doctor --output json`;
- target-specific plan output;
- apply result;
- follow-up idempotent plan;
- Databricks UI screenshot with secrets and private data removed.

Use structured error codes from DataMuru output when reporting issues.
