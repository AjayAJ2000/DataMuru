# Testing and Release

The alpha repository already includes a baseline test suite and validation workflow.

## Current automated checks

- unit tests under `tests/unit/`
- end-to-end bootstrap coverage under `tests/e2e/`
- CLI validation through `datamuru validate`
- Python 3.10, 3.11, 3.12, and 3.13 compatibility in GitHub Actions
- Ruff static checks
- strict MkDocs builds
- wheel and source-distribution metadata checks

## Practical commands

Run the tests:

```bash
python -m ruff check datamuru tests
python -m pytest
python -m mkdocs build --strict
python -m build
python -m twine check dist/*
```

Run config validation:

```bash
python -m datamuru.cli.main validate --config datamuru.yml
```

## Release hygiene expectation

As the product matures, each release should verify:

- code behavior
- documentation accuracy
- schema alignment
- example correctness

For a SaaS-grade product, release confidence is as much about trust and clarity as it is about passing code paths.

Live Databricks tests are intentionally not executed from public CI because they require customer-controlled credentials and can mutate cloud resources. Run the enterprise test sequence in a dedicated non-production account and workspace.
