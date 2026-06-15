<div class="dm-docs-hero">
  <img src="assets/datamuru-mark.svg" alt="DataMuru Vel Eye logo">
  <div>
    <h1>DataMuru Documentation</h1>
    <p>Provider-agnostic data infrastructure, governed by design.</p>
  </div>
</div>

DataMuru is a declarative data infrastructure and governance framework for
Databricks. You describe the platform resources and access rules that you want.
DataMuru validates the configuration, compares it with state and supported live
resources, shows a deterministic plan, and applies approved changes.

```powershell
pip install datamuru
datamuru validate --config datamuru.yml
datamuru doctor --config datamuru.yml
datamuru plan --config datamuru.yml
```

!!! warning "Alpha software"
    DataMuru `0.1.0a0` is an alpha release. It supports real Databricks
    operations for the resource types listed in the
    [capability reference](reference/capabilities.md), but it is not yet a
    complete production platform. Test with non-production resources first.

## Choose your goal

| Goal | Start here |
| --- | --- |
| Evaluate DataMuru without cloud access | [Five-minute local quickstart](getting-started/quickstart.md) |
| Connect a Databricks workspace safely | [Connect a Databricks workspace](tutorials/connect-databricks.md) |
| Try Databricks Free Edition | [Databricks Free Edition](getting-started/databricks-free-edition.md) |
| Create a catalog and schemas | [Provision a catalog and schemas](tutorials/catalog-and-schemas.md) |
| Adopt existing Databricks resources | [Import an existing workspace](tutorials/import-existing-workspace.md) |
| Look up a command or field | [CLI reference](reference/cli.md) |
| Diagnose a failure | [Troubleshooting](guides/troubleshooting.md) |
| Evaluate product and edition scope | [Platform overview](product/platform-overview.md) |

## What you can manage today

The OSS alpha includes:

- configuration loading and semantic validation;
- local state, deterministic plans, targeted operations, and saved plans;
- live Databricks catalog and schema reconciliation;
- catalog creation with a managed location or Databricks default storage;
- Unity Catalog grants compiled from DataMuru RBAC definitions;
- read-only discovery and YAML generation for existing workspaces;
- taxonomy, RBAC, and masking definitions;
- a Python API over the same engine used by the CLI.

Some resource types are modeled locally but do not yet have live provider
effects. Account-level identity lifecycle is an Enterprise capability and also
depends on Databricks account SCIM availability. See
[Current capabilities and limits](reference/capabilities.md) before planning a
rollout.

## The operating loop

1. **Write configuration.** Keep project, provider, workspace, environment, and
   governance concerns in separate YAML files.
2. **Validate.** Catch missing files, unsupported values, and unsafe edition
   combinations before contacting a provider.
3. **Run doctor.** Verify credentials, connectivity, SQL warehouse requirements,
   and provider capabilities.
4. **Plan.** Review create, update, no-op, and destroy actions.
5. **Apply deliberately.** Prefer narrow targets during evaluation and saved
   plans in shared environments.
6. **Re-plan.** A successful idempotent run should report no required changes.

## Documentation conventions

- Commands use `datamuru`, the console script installed from PyPI.
- Paths are relative to the directory containing `datamuru.yml` unless stated
  otherwise.
- Placeholder values use names such as `your-workspace` and must be replaced.
- Destructive and live-cloud steps are marked explicitly.
- Every task states prerequisites, expected results, and a recovery path.

## Get help

Search this site first. If the problem remains:

- review [Troubleshooting](guides/troubleshooting.md);
- collect `datamuru doctor --output json` and the structured error code;
- choose the appropriate route in [Support and feedback](operations/support.md)
  without including tokens, customer data, or private workspace details.
