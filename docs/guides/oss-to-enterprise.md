# Move from OSS to Enterprise

DataMuru OSS is the evaluation and open-core foundation. DataMuru Enterprise
adds identity lifecycle, private provider extensions, richer import/adoption,
multi-workspace operating controls, support, and commercial entitlement.

## Recommended adoption path

1. Install OSS in a sandbox and validate project structure.
2. Connect one non-production workspace in `live-readonly`.
3. Run import discovery and generate an import review suite.
4. Review generated workspace, RBAC, taxonomy, and masking files with platform
   owners.
5. Enable Enterprise features only after the target account and identity
   permissions are confirmed.
6. Move to `live-apply` only for targeted, reviewed resources.

## Enterprise auth options

PAT auth remains useful for quick tests, but Enterprise pilots should prefer
organization-approved auth:

```yaml
provider:
  cloud: azure
  auth_type: databricks-cli
  profile: enterprise-dev
  execution_mode: live-readonly
  sql_warehouse_id_env: DATABRICKS_SQL_WAREHOUSE_ID
```

DataMuru reads `~/.databrickscfg` by default. You can override it with:

```powershell
$env:DATABRICKS_CONFIG_FILE="<path-to-your-databrickscfg>"
$env:DATABRICKS_CONFIG_PROFILE="enterprise-dev"
```

For managed identity, SAML/SSO, OAuth M2M, and customer-specific token
brokerage, use the Enterprise provider extension path. OSS exposes the
configuration boundary; Enterprise owns the secure credential acquisition and
policy controls.

## Generate a brownfield review suite

Run this in a sandbox or read-only enterprise workspace:

```powershell
datamuru import generate `
  --config datamuru.yml `
  --catalog existing_catalog `
  --suite-out .\import-review
```

The suite includes:

| File | Purpose |
| --- | --- |
| `workspaces/imported-dev.yml` | Catalogs, schemas, principals, and memberships discovered from the workspace. |
| `governance/rbac.imported.yml` | Starter RBAC roles and assignments generated from live grants. |
| `governance/taxonomy.imported.yml` | Placeholder taxonomy for curation. |
| `governance/masking.imported.yml` | Placeholder masking policy hooks for review. |

Import generation does not mutate Databricks. It produces reviewable files that
teams can copy into the main project after cleanup.

## Enterprise validation checklist

- `datamuru doctor` succeeds with the approved auth method.
- Account SCIM is available before testing managed users, groups, service
  principals, or group memberships.
- A SQL warehouse is configured before grant import or live ACL apply.
- Generated files do not contain system-owned catalogs, schemas, or groups
  unless `--include-system` was intentionally used.
- State adoption uses explicit `--target` values and is reviewed before
  `--auto-approve`.

## Snowflake migration note

Snowflake is now represented as a first-class provider for state-only planning
and live-readonly database/schema discovery. Use OSS to inspect bounded
Snowflake trial or sandbox inventory:

```powershell
pip install "datamuru[snowflake]"
datamuru import discover --config datamuru.yml --catalog FINANCE
```

Live Snowflake apply, destroy, identity import, and grant import remain
Enterprise-hardening work and should be tested with controlled credentials
before production rollout.
