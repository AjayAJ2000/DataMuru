# Installation

This repository supports three installation stories:

- local source installation for contributors and evaluators
- PyPI installation for users and teams
- provider extras for cloud-specific integrations

## Runtime assumptions

- Python `3.10+`
- Git
- A shell environment capable of running Python CLI commands

## Install from source

```bash
python -m pip install -e .
```

## Install from PyPI

Once the package is published, the preferred team installation path should be:

```bash
pip install datamuru
```

For Databricks SDK support:

```bash
pip install "datamuru[databricks]"
```

For pinned production or shared platform usage, prefer explicit version pinning:

```bash
pip install "datamuru==0.1.0a0"
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
python -m mkdocs build --strict
```

## Notes for teams

- The alpha implementation is intentionally local-first.
- No external data-platform toolchain is required to run the framework scaffold.
- Live provider mutations require explicit `execution_mode: live-apply`.
- Pin alpha package versions in shared and enterprise environments.
- Keep credentials in environment variables or an external secret manager; never place tokens in YAML.
