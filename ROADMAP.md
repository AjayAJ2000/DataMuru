# DataMuru Product Roadmap

This roadmap turns the PRD into the next concrete build sequence for the repository.

## Current stage

`v0.1 alpha bootstrap`

Already in place:

- shared Python package skeleton
- local state, planning, apply, and destroy
- Azure-first Databricks provider scaffold
- taxonomy, RBAC, and masking compilation
- MkDocs documentation baseline
- PyPI-oriented package metadata baseline

## Next step

Build the product as a shared core with two edition tracks:

- `DataMuru OSS`
- `DataMuru Enterprise`

This follows the PRD more closely than creating two separate product forks. The codebase stays shared, while edition-specific features, packaging, examples, and commercial surfaces evolve in parallel.

## Parallel build tracks

### Shared Core

- strengthen config contracts
- add edition-aware feature gating
- improve provider execution model
- add saved-plan apply
- add stronger schema coverage

### DataMuru OSS

- harden the open-source local and single-workspace journey
- keep governance, planning, and local developer workflows strong
- prepare clean PyPI and docs experience for community adoption

### DataMuru Enterprise

- model enterprise-only features in config and validation
- add multi-workspace and hosted-control-plane scaffolding
- prepare hooks for compliance reporting, SIEM, and advanced orchestration

## Milestones

### Milestone 1

- edition-aware validation
- OSS and Enterprise starter folders
- roadmap and product separation docs

### Milestone 2

- richer provider contract
- saved-plan apply
- environment overlays
- edition-aware CLI inspection

### Milestone 3

- real Databricks API integration for supported alpha resources
- capability-aware Enterprise identity and group membership lifecycle
- cloud backend state abstraction
- enterprise orchestration hooks

### Milestone 4

- import discovery and configuration generation
- broader governance enforcement
- release automation for PyPI and docs publishing

Status: import discovery/config generation and release automation are implemented. State adoption, conflict-safe brownfield reconciliation, and broader governance enforcement remain open.
