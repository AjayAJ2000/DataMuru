# Contributing to DataMuru

DataMuru uses one shared Python core with OSS and Enterprise edition boundaries enforced through configuration and runtime capabilities.

## Development setup

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e ".[dev,docs,test]"
```

## Required checks

```bash
python -m ruff check datamuru tests
python -m pytest
python -m mkdocs build --strict
python -m build
python -m twine check dist/*
```

Do not commit credentials, `.datamuru` state, generated package distributions, built documentation, or environment-specific live configuration.

## Change discipline

- Add or update tests for behavioral changes.
- Keep public configuration, schemas, examples, and documentation aligned.
- Preserve conservative deletion defaults for cloud and identity resources.
- Document edition boundaries when adding Enterprise-only behavior.
- Update `CHANGELOG.md` for user-visible changes.
