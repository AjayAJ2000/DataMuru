# DataMuru Documentation

<div class="dm-docs-hero">
  <img src="assets/datamuru-mark-canva.png" alt="DataMuru Vel Eye logo" width="144" height="144">
  <div>
    <p>Provider-agnostic data infrastructure, governed by design.</p>
  </div>
</div>

DataMuru is a provider-agnostic declarative data infrastructure and governance
framework. You describe the platform resources, access rules, and governance
intent that you want. DataMuru validates the configuration, compares it with
state and supported live resources, shows a deterministic plan, and applies
approved changes.

Databricks is the first live provider adapter in the current alpha. The product
direction is broader: a shared control layer for data platform resources,
governance, brownfield adoption, and eventually multi-cloud execution.

```powershell
pip install datamuru
datamuru validate --config datamuru.yml
datamuru doctor --config datamuru.yml
datamuru plan --config datamuru.yml
```

!!! warning "Alpha software"
    DataMuru `0.3.2a0` is an alpha release. It supports real Databricks
    operations for the resource types listed in the
    [capability reference](reference/capabilities.md), but it is not yet a
    complete production platform. Test with non-production resources first.

## Choose your goal

| Goal | Start here |
| --- | --- |
| Decide whether DataMuru fits your team | [Evaluation checklist](getting-started/evaluation-checklist.md) |
| Evaluate DataMuru without cloud access | [Five-minute local quickstart](getting-started/quickstart.md) |
| Connect a Databricks workspace safely | [Connect a Databricks workspace](tutorials/connect-databricks.md) |
| Try Databricks Free Edition | [Databricks Free Edition](getting-started/databricks-free-edition.md) |
| Create a catalog and schemas | [Provision a catalog and schemas](tutorials/catalog-and-schemas.md) |
| Plan an enterprise pilot | [Enterprise rollout playbook](operations/enterprise-rollout-playbook.md) |
| Adopt existing Databricks resources | [Import an existing workspace](tutorials/import-existing-workspace.md) |
| Look up a command or field | [CLI reference](reference/cli.md) |
| Diagnose a failure | [Troubleshooting](guides/troubleshooting.md) |
| Evaluate product and edition scope | [Platform overview](product/platform-overview.md) |

## Who this documentation is for

| Reader | What to read first |
| --- | --- |
| New evaluator | [Choose a path](getting-started/overview.md), then [Evaluation checklist](getting-started/evaluation-checklist.md). |
| Platform engineer | [How DataMuru works](concepts/how-datamuru-works.md), [Lifecycle model](concepts/lifecycle-model.md), and [Review and apply changes](guides/plan-and-apply.md). |
| Databricks operator | [Authenticate to Databricks](guides/authentication.md), [Execution modes](guides/execution-modes.md), and [Catalogs and schemas](guides/catalogs-and-schemas.md). |
| Governance owner | [Governance model](governance/overview.md), [RBAC model](governance/rbac.md), and [ACL guidelines](operations/acl-guidelines.md). |
| Library contributor | [Architecture overview](architecture/overview.md), [Library architecture](architecture/library-architecture.md), and [Command lifecycle](architecture/command-lifecycle.md). |
| Enterprise pilot team | [Product requirements summary](product/product-requirements-summary.md), [Enterprise rollout playbook](operations/enterprise-rollout-playbook.md), and [Enterprise testing runbook](product/enterprise-testing.md). |

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

## How the docs are organized

- **Start** helps you choose a safe evaluation path.
- **Tutorials** walk through complete tasks from blank project to live provider
  behavior.
- **How-to guides** answer specific operator questions.
- **Concepts** explain the mental model behind state, lifecycle, targets, and
  governance.
- **Architecture** explains the package design, command lifecycle, provider
  contract, and extension points.
- **Reference** defines command, config, result, and error contracts.
- **Operations** covers team adoption, release, security, production readiness,
  and enterprise rollout practices.
- **Product** explains edition boundaries, requirements, roadmap, packaging,
  and enterprise testing.

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
