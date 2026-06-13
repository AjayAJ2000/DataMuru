# Architecture Overview

The alpha repository is organized to reflect the long-term shape of the framework while keeping implementation scope tight and PyPI-friendly.

## Major layers in the current codebase

### Core

Located in `datamuru/core/`, this layer is now split into product-oriented runtime packages:

- `config/`
- `state/`
- `plan/`
- `apply/`
- `importer/`

Together these packages provide:

- config loading
- validation
- state management
- deterministic planning
- apply and destroy orchestration
- brownfield discovery and configuration-generation workflows

### Providers

Located in `datamuru/providers/`, this layer provides:

- a provider interface
- a Databricks provider factory
- an Azure-first Databricks implementation with live support for selected resources

### Governance

Located in `datamuru/governance/`, this layer provides:

- taxonomy compilation
- RBAC compilation
- masking compilation

### CLI

Located in `datamuru/cli/`, this layer exposes the current command surface through thin Click command modules with shared Rich output and structured error rendering.

## Architectural intent

The repository is intentionally structured so future features can be added without collapsing boundaries:

- the CLI should remain thin
- the core engine should own orchestration semantics
- providers should own platform-specific resource modeling
- governance should remain composable and separable

## Current implementation boundary

The Databricks provider performs real API operations for supported catalogs,
schemas, Unity Catalog grants, and discovery workflows. Other resources remain
local-only or Enterprise-only. The
[capability reference](../reference/capabilities.md) is the source of truth.

## Product direction

This structure is also the basis for the commercial model defined in the PRD:

- one shared codebase
- one OSS distribution path
- one Enterprise expansion path
- explicit edition-aware feature boundaries
