# Platform Overview

DataMuru is designed to become a productized control layer for enterprise data
platform infrastructure. The long-term product thesis is that data platform
assembly work should be standardized, versioned, and governed in the same way
cloud infrastructure became standardized through infrastructure-as-code.

Today, platform teams often combine manual Databricks UI changes, notebooks,
scripts, IAM tickets, spreadsheet-based access reviews, and provider-specific
runbooks. DataMuru exists to move that work into one reviewable lifecycle:

```text
declare -> validate -> diagnose -> plan -> apply -> observe -> adopt -> govern
```

## Product direction

DataMuru aims to give platform teams a single control plane model for:

- Workspace and platform topology
- Governance taxonomy and policy compilation
- Access-control baselines
- Repeatable project bootstrapping
- Future lifecycle workflows such as import, policy rollout, and compliance reporting

## Product pillars

| Pillar | What it means in the product |
| --- | --- |
| Declarative platform intent | Teams describe catalogs, schemas, access, and governance in configuration. |
| Deterministic change review | Plans explain what will be created, updated, skipped, or destroyed. |
| Provider-backed execution | Provider adapters perform supported live operations. |
| Governance-aware modeling | Taxonomy, RBAC, and masking are core concepts, not afterthoughts. |
| Brownfield adoption | Existing resources can be discovered, generated into YAML, and adopted deliberately. |
| Open-core expansion | OSS owns shared contracts; Enterprise extends high-scale and regulated workflows. |

## What DataMuru is not

DataMuru is not intended to be:

- a replacement for Databricks itself;
- a generic workflow scheduler;
- a data transformation framework;
- a dashboarding product;
- a hidden wrapper around Terraform;
- a one-off script generator.

It is a product framework for data infrastructure and governance lifecycle
management.

## Product principles

- **Python-first**: the CLI and automation layer are built around a typed Python core.
- **Declarative-first**: configuration expresses desired state, not shell choreography.
- **Governance-first**: governance is not a sidecar feature; it influences resource modeling.
- **Provider-ready**: platform-specific logic lives behind an implementation contract.
- **Enterprise-credible**: documentation, schemas, and change surfaces must be clear enough for global teams and implementation partners.

## Current alpha positioning

The current repository is a bootstrap foundation for:

- A stable contributor baseline
- A product documentation baseline
- A future path to richer provider logic and enterprise-grade workflows

This means the alpha should be treated as the beginning of the framework, not the full market promise yet.

## Product maturity model

| Stage | What users should expect |
| --- | --- |
| Local evaluation | Full config/plan/apply loop against local state. |
| Workspace smoke test | Live Databricks catalog/schema and grant operations on test resources. |
| Brownfield review | Discovery and generated YAML for supported resources. |
| Enterprise pilot | Identity and multi-team operating controls in sandbox environments. |
| Production rollout | Requires stronger state backends, policy maturity, and team controls. |

Use the [evaluation checklist](../getting-started/evaluation-checklist.md) and
[enterprise rollout playbook](../operations/enterprise-rollout-playbook.md) to
choose the right maturity stage.
