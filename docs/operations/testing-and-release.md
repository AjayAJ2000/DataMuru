# Testing and Release

The alpha repository already includes a baseline test suite and validation workflow.

## Current automated checks

- unit tests under `tests/unit/`
- end-to-end bootstrap coverage under `tests/e2e/`
- CLI validation through `datamuru validate`
- Python 3.11, 3.12, and 3.13 compatibility in GitHub Actions
- Ruff static checks
- strict MkDocs builds
- wheel and source-distribution metadata checks

## Practical commands

Run the tests:

```bash
python -m ruff check datamuru tests
python -m pytest
NO_MKDOCS_2_WARNING=1 python -m mkdocs build --strict
python -m build
python -m twine check dist/*
```

Material for MkDocs `9.7.2` and newer prints an upstream notice about the
future MkDocs `2.0` direction. DataMuru pins MkDocs to `>=1.6,<2`, so the notice
is not a failing upgrade requirement. Set `NO_MKDOCS_2_WARNING=1` for local and
CI documentation builds to keep logs focused on DataMuru warnings and errors.

PowerShell equivalent:

```powershell
$env:NO_MKDOCS_2_WARNING = "1"
python -m mkdocs build --strict
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
