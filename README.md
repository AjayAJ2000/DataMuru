<p align="center">
  <img src="docs/assets/datamuru-mark-canva.png" alt="DataMuru logo" width="240" height="240">
</p>

<h1 align="center">DataMuru</h1>

<p align="center"><strong>Provider-agnostic data infrastructure, governed by design.</strong></p>

[![CI](https://github.com/AjayAJ2000/DataMuru/actions/workflows/ci.yml/badge.svg)](https://github.com/AjayAJ2000/DataMuru/actions/workflows/ci.yml)
[![Documentation](https://github.com/AjayAJ2000/DataMuru/actions/workflows/docs.yml/badge.svg)](https://ajayaj2000.github.io/DataMuru/)
[![PyPI](https://img.shields.io/pypi/v/datamuru.svg)](https://pypi.org/project/datamuru/)
![License](https://img.shields.io/badge/License-Apache%202.0-0D7377)
[![Python](https://img.shields.io/pypi/pyversions/datamuru.svg)](https://pypi.org/project/datamuru/)

DataMuru is an Apache-2.0, Python-first data infrastructure framework.
It provisions and governs provider-backed data estates from declarative configuration.
This public repository is the canonical home of the DataMuru Open Source Edition,
the shared configuration contract, the `datamuru` PyPI package, and the public documentation.

This repository contains the `v0.3 alpha` implementation with the following scope:

- Foundation layer: config loading, validation, local state, planning, apply, and destroy.
- Azure-first Databricks provider abstraction with multi-cloud-ready interfaces.
- Basic governance compilation: taxonomy, RBAC, and masking integration points.
- Core CLI surface: `init`, `validate`, `plan`, `apply`, and `destroy`.
- MkDocs-based product documentation written from an international SaaS product perspective.
- Live Databricks catalog, schema, ACL, import-discovery, and supported identity workflows.

## Current stage

DataMuru is currently in the `v0.3 alpha` stage.

The package and CLI execute supported live Databricks operations when `execution_mode: live-apply` is configured. Alpha support currently covers catalogs, schemas, Unity Catalog ACLs, import discovery/config generation, and capability-aware account SCIM identity operations.

## Delivery status

Product execution is tracked in the private
[DataMuru Product Roadmap](https://github.com/users/AjayAJ2000/projects/1)
GitHub Project. The repository snapshot is maintained in
[PROJECT_STATUS.md](PROJECT_STATUS.md), including readiness, risks, milestones,
completed work, blocked work, and next recommended actions.

## Open-core model

- **DataMuru OSS:** this public Apache-2.0 repository and PyPI package.
- **DataMuru Enterprise:** a private extension repository for paid capabilities such as multi-workspace orchestration, advanced compliance automation, hosted services, SSO/SAML, SIEM integrations, and SLA-backed operations.

Enterprise extends the public core; it does not maintain a competing fork of the core configuration model or CLI.

## Design constraints

- Multi-cloud is an architectural requirement, but not a parity requirement for the alpha slice.
- `open-source` vs `enterprise` is the only runtime packaging boundary.
- Zero external data-tool runtime dependencies means no Terraform, dbt, Airflow, Great Expectations, Fivetran, or Airbyte required for the framework to operate.

## Quick start

```bash
pip install datamuru
datamuru validate --config datamuru.yml
datamuru doctor --config datamuru.yml
datamuru plan --config datamuru.yml
```

## Installation

From PyPI:

```bash
pip install datamuru
```

## Documentation

This repository now includes a full MkDocs documentation site.

- MkDocs config: [mkdocs.yml](mkdocs.yml)
- Docs source: [docs](docs/)
- Published documentation: [ajayaj2000.github.io/DataMuru](https://ajayaj2000.github.io/DataMuru/)
- Support and documentation feedback:
  [Support and feedback](https://ajayaj2000.github.io/DataMuru/operations/support/)

To work on the documentation locally:

```bash
python -m pip install -e ".[docs]"
python -m mkdocs serve
```

## Product usage guidance

For operator guidance and rollout practices, start with:

- [Product Usage Guidelines](docs/operations/usage-guidelines.md)
- [Team Adoption Guidelines](docs/operations/team-adoption-guidelines.md)

## Trying it with Databricks Free Edition

If you want to try the framework with your own Databricks personal workspace, start here:

- [Databricks Free Edition Setup](docs/getting-started/databricks-free-edition.md)

For package-oriented team usage, also read:

- [Packaging and Distribution](docs/product/packaging-and-distribution.md)
- [Product Usage Guidelines](docs/operations/usage-guidelines.md)

## Repository standards

- `datamuru/`: shared installable Python package
- `docs/`: versioned product documentation published through GitHub Pages
- `schemas/`: public configuration contracts
- `tests/`: unit, provider-contract, and end-to-end tests
- `.github/workflows/`: CI, documentation deployment, link validation, and
  trusted PyPI publishing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the required local quality gate.
