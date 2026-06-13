# Contribute to DataMuru

Contributions should keep code, schemas, examples, tests, and documentation
aligned.

## Set up

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,docs,test]"
```

## Run the quality gate

```powershell
python -m ruff check datamuru tests
python -m pytest -q
python -m mkdocs build --strict
python -m build
python -m twine check dist\*
```

## Change requirements

- Add tests for behavior changes.
- Update public reference pages for contract changes.
- Add or update a task guide when the user workflow changes.
- Keep examples sanitized and runnable.
- Update `CHANGELOG.md` for user-visible changes.
- Do not add proprietary Enterprise implementation to the OSS repository.

Read the [documentation style guide](documentation-style-guide.md) before
editing user documentation.
