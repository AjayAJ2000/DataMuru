# DataMuru Documentation

DataMuru is a Python-first enterprise data infrastructure framework for teams that need to provision, govern, and operate a Databricks-centered data platform from declarative configuration.

This documentation is written from the perspective of an international SaaS product:

- Clear platform positioning for engineering leaders, platform teams, and implementation partners.
- Practical onboarding guidance for teams evaluating the framework in development or early production.
- Reference-grade documentation for the alpha implementation now in this repository.

## What DataMuru is

DataMuru turns repeated enterprise data platform assembly work into productized infrastructure:

- Declarative platform configuration
- Deterministic planning and apply workflows
- Provider-based platform abstraction
- Governance-first resource modeling
- Product-local documentation and schemas that can evolve with the codebase

## Current implementation status

This repository currently tracks the `v0.1 alpha`:

- Foundation layer: config loading, validation, local state, planning, apply, and destroy
- Azure-first Databricks provider abstraction
- Basic governance compilation for taxonomy, RBAC, and masking
- CLI surface: `init`, `validate`, `plan`, `apply`, and `destroy`
- Live Databricks catalogs, schemas, Unity Catalog ACLs, import discovery, and capability-aware identity management

## Who this is for

- Platform engineering teams building governed Databricks environments
- Data platform architects standardizing workspace and governance setup
- Systems integrators who need a repeatable project baseline
- Developers contributing to the DataMuru framework itself

## Documentation map

- Start with **Getting Started** if you want to understand what exists today and how to run it.
- Read **Product** for positioning, edition boundaries, and roadmap context.
- Use **Architecture** and **Reference** when implementing or extending the framework.
- Use **Operations** for validation, release hygiene, and contributor workflows.

## Distribution

DataMuru is distributed as the `datamuru` Python package. The repository automatically validates supported Python versions, builds package distributions, publishes tagged GitHub releases to PyPI through Trusted Publishing, and deploys these docs to GitHub Pages.
