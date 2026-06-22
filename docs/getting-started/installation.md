# Installation

This repository supports three installation stories:

- local source installation for contributors and evaluators
- PyPI installation for users and teams
- provider extras for cloud-specific integrations

## Runtime assumptions

- Python `3.11+`
- Git
- A shell environment capable of running Python CLI commands

!!! info "Current documented release"
    The current packaged release documented for installation is DataMuru
    `0.4.0a0`. Pin this version for reproducible alpha evaluations.

## Install from source

```bash
python -m pip install -e .
```

## Install from PyPI

For quick personal evaluation:

```bash
pip install datamuru
```

For Databricks SDK support:

```bash
pip install "datamuru[databricks]"
```

For pinned production or shared platform usage, prefer explicit version pinning:

```bash
pip install "datamuru==0.4.0a0"
```

For internal rollout guides and enterprise onboarding, document the exact supported version instead of relying on `latest`.

For contributor and release tooling:

```bash
python -m pip install -e ".[dev,docs,test]"
```

## Documentation dependencies

The repository includes MkDocs configuration for a full product-style documentation site.

Use the docs extra to install the site tooling:

```bash
python -m pip install -e .[docs]
```

## Build the documentation locally

```bash
python -m mkdocs serve
```

To produce a static build:

```bash
NO_MKDOCS_2_WARNING=1 python -m mkdocs build --strict
```

## Notes for teams

- The alpha implementation is intentionally local-first.
- No external data-platform toolchain is required to run the framework scaffold.
- Live provider mutations require explicit `execution_mode: live-apply`.
- Pin alpha package versions in shared and enterprise environments.
- Keep credentials in environment variables or an external secret manager; never place tokens in YAML.
