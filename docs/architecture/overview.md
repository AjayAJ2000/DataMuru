# Architecture Overview

DataMuru is organized as an installable Python library, a CLI, provider
adapters, governance compilers, public schemas, examples, tests, and product
documentation. The architecture is shaped for a product framework rather than a
one-off automation script.

For the detailed package-level explanation, read
[Library architecture](library-architecture.md).

## Architectural goals

The architecture is designed to support:

- PyPI distribution for OSS users;
- Enterprise extension without forking the core contracts;
- provider-specific behavior without leaking provider APIs into the planner;
- deterministic plans that are reviewable by humans and automation;
- conservative brownfield adoption;
- governance intent that participates in the same lifecycle as infrastructure;
- a CLI that remains thin over a reusable Python API.

The core product promise is not "run a Databricks API call." It is "give data
platform teams a repeatable operating model for declaring, reviewing, applying,
and governing platform changes." That is why the architecture treats
configuration, planning, state, provider execution, governance, documentation,
and packaging as one product system.

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
- saved-plan safety checks
- structured apply outcomes

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
- errors should carry stable codes and recovery guidance
- docs and schemas should evolve with runtime behavior

## Design boundaries

DataMuru intentionally keeps these concerns separate:

| Concern | Owned by |
| --- | --- |
| Command parsing and terminal output | CLI layer |
| Config loading and validation | Core config layer |
| Desired/current state comparison | Plan layer |
| Provider mutation and observation | Provider layer |
| Taxonomy, RBAC, and masking compilation | Governance layer |
| State persistence | State backend layer |
| OSS/Enterprise feature boundary | Edition layer |

## Current implementation boundary

The Databricks provider performs real API operations for supported catalogs,
schemas, Unity Catalog grants, and discovery workflows. Other resources remain
local-only or Enterprise-only. The
[capability reference](../reference/capabilities.md) is the source of truth.

Hosted control plane work starts as an explicit OSS contract boundary. The
`datamuru enterprise control-plane contract` command builds a redacted local
handoff artifact with activation readiness, state posture, feature flags, and
required hosted follow-up actions. The OSS runtime does not provision tenants,
activate licenses, or execute shared remote state; those responsibilities stay
behind Enterprise extensions or a hosted service.

The hosted architecture itself is also exportable through
`datamuru enterprise control-plane architecture`. That command emits a versioned
reference contract covering components, data flows, extension points, trust
boundaries, decisions, backlog, and non-goals. The human-readable companion page
is [Hosted control plane architecture](hosted-control-plane.md).

## Architecture map

| Area | Why it exists | What to read |
| --- | --- | --- |
| Library architecture | Explains the importable package, runtime flow, dependencies, and extension points. | [Library architecture](library-architecture.md) |
| Command lifecycle | Explains what happens when users run validate, doctor, plan, apply, destroy, and import. | [Command lifecycle](command-lifecycle.md) |
| Core runtime | Explains config, state, planning, apply, and importer packages. | [Core runtime](core-runtime.md) |
| Provider model | Explains how platform-specific adapters fit into a cloud-neutral core. | [Provider model](provider-model.md) |
| Configuration model | Explains how root, provider, workspace, environment, and governance files relate. | [Configuration model](configuration-model.md) |
| Hosted control plane | Explains the Enterprise hosted architecture, extension points, and trust boundaries. | [Hosted control plane](hosted-control-plane.md) |
| Governance architecture | Explains taxonomy, RBAC, masking, and provider grant compilation. | [Governance architecture](../governance/overview.md) |

## How to read the architecture docs

- Start with this page for the product-level shape.
- Read [Library architecture](library-architecture.md) for the package map and
  execution flow.
- Read [Command lifecycle](command-lifecycle.md) for command-by-command runtime
  behavior.
- Read [Core runtime](core-runtime.md) when changing config, state, plan,
  apply, or import behavior.
- Read [Provider model](provider-model.md) when adding or extending platform
  adapters.
- Read [Configuration model](configuration-model.md) when changing YAML
  contracts or validation.

## Product direction

This structure is also the basis for the commercial model defined in the PRD:

- one shared codebase
- one OSS distribution path
- one Enterprise expansion path
- explicit edition-aware feature boundaries
