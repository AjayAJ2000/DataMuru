# Product Requirements Summary

This page summarizes the product intent behind the current implementation. It
is not a replacement for the full PRD; it gives engineers, operators, and
evaluators a shared product lens while reading the docs.

## Product problem

Data platform teams often assemble infrastructure, governance, access control,
and operating procedures through a mixture of scripts, tickets, notebooks,
manual UI changes, and provider-specific conventions. That creates drift and
makes it hard to answer basic questions:

- What should exist?
- Who approved the change?
- What changed between environments?
- Which resources are governed by platform policy?
- Which resources are manually managed exceptions?

DataMuru addresses this by making data platform intent declarative,
reviewable, and executable through a Python-first control layer.

## Primary users

| User | Job to be done |
| --- | --- |
| Platform engineer | Define repeatable data platform resources and apply them safely. |
| Data governance lead | Connect taxonomy, RBAC, and masking intent to platform resources. |
| Security reviewer | Understand permissions before they are applied. |
| Data product team | Request or review governed platform changes without learning every provider API. |
| Enterprise operator | Run validated, auditable changes across controlled environments. |

## Product principles

- **Provider-agnostic core:** provider-specific APIs belong behind adapters.
- **Azure-first implementation:** Databricks on Azure is the first live path,
  but it must not become the product boundary.
- **Declarative configuration:** YAML describes desired state; commands execute
  a predictable lifecycle.
- **Governance by design:** RBAC, classification, taxonomy, and masking are
  first-class model concerns.
- **Safety before convenience:** validate, doctor, plan, saved plans, targets,
  and explicit destroy confirmation are part of the product contract.
- **OSS and Enterprise clarity:** OSS owns the shared package, CLI, schemas,
  docs, and core contracts; Enterprise extends those contracts.

## Current alpha scope

The current alpha focuses on:

- project scaffolding;
- validation and diagnostics;
- local state;
- deterministic planning;
- targeted apply and destroy;
- saved-plan safety checks;
- Databricks catalog and schema live operations;
- Databricks default-storage catalog creation through SQL warehouses;
- RBAC grant compilation for Unity Catalog;
- import discovery, YAML generation, and conservative state adoption;
- basic Enterprise identity lifecycle hooks where account SCIM is available.

## Out of scope today

These remain roadmap items:

- production cloud state backends;
- full multi-workspace orchestration;
- AWS and GCP live parity;
- ingestion pipeline management;
- modeling workflow management;
- observability integrations;
- compliance report generation;
- transactional rollback for every provider operation;
- hosted control plane.

## Evaluation promise

A successful alpha evaluation should prove that DataMuru can:

1. express platform intent in a readable configuration layout;
2. validate that layout before provider calls;
3. compare desired and observed state;
4. create a small live target safely;
5. re-plan idempotently;
6. preserve enough structured output for audit and troubleshooting.

Do not evaluate the alpha as if every PRD capability is complete. Evaluate
whether the foundation is credible, safe, and extensible.
