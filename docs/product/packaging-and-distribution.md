# Packaging and Distribution

DataMuru is intended to be consumed as a Python package, not only as a source repository.

## Distribution model

The intended package distribution path is:

- publish to PyPI for broad installability
- keep the CLI entrypoint available through the package
- keep the Python API importable for automation and internal tooling

## Repository readiness

The alpha already includes:

- package metadata in `pyproject.toml`
- a console script entrypoint for `datamuru`
- optional extras for provider, test, development, and docs tooling
- Python 3.11 through 3.13 CI
- wheel and source-distribution validation
- GitHub Pages documentation deployment
- OIDC-based PyPI Trusted Publishing

## Release model

- Merge only after CI succeeds.
- Keep `pyproject.toml` and `datamuru.__version__` aligned.
- Create a GitHub release tagged with the package version, such as `v0.5.0a0`.
- The release workflow verifies the tag, builds the distributions, validates metadata, and publishes to PyPI.
- Use a protected `pypi` GitHub environment and PyPI Trusted Publisher instead of a stored API token.

## Recommended consumption modes

### Individual evaluation

Install from source or a pre-release package and validate locally.

### Team rollout

Pin explicit versions in requirements files or internal package registries.

### Enterprise platform use

Use release-tagged versions only and pair package rollout with matching documentation and config schema versions.

## Documentation requirement

Because teams will consume DataMuru as a package, packaging and installation documentation should be treated as first-class product docs, not as an afterthought for contributors only.

See [Publishing](../operations/publishing.md) for the maintainer setup and release checklist.
