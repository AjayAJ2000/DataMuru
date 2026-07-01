# Publishing DataMuru

DataMuru uses GitHub Actions for package validation, GitHub Pages deployment, and tokenless PyPI publication.

## One-time GitHub Pages setup

1. Open the repository on GitHub.
2. Go to **Settings > Pages**.
3. Under **Build and deployment**, set **Source** to **GitHub Actions**.
4. Push the repository changes to `main`.
5. Run the **Documentation** workflow if it does not start automatically.
6. Verify the site at `https://ajayaj2000.github.io/DataMuru/`.

The workflow builds MkDocs with strict validation, uploads the generated `site` directory as a Pages artifact, and deploys through the protected `github-pages` environment.

The documentation workflow grants Pages permissions to both the configuration/build job and deployment job. A repository with Pages disabled must still be enabled once through repository settings or the Pages API before `actions/configure-pages` can read its site metadata.

## One-time PyPI Trusted Publisher setup

Create a pending publisher if the `datamuru` project does not yet exist on PyPI, or add a publisher to the existing project.

Use these exact values:

| Field | Value |
| --- | --- |
| PyPI project name | `datamuru` |
| GitHub owner | `AjayAJ2000` |
| GitHub repository | `DataMuru` |
| Workflow filename | `release.yml` |
| Environment name | `pypi` |

In GitHub, create an environment named `pypi`. For stronger release governance, require reviewer approval for that environment.

No `PYPI_TOKEN` secret is required. The release job requests a short-lived OIDC identity token and exchanges it through PyPI Trusted Publishing.

## Release checklist

1. Update the version in `pyproject.toml` and `datamuru/__init__.py`.
2. Update `CHANGELOG.md`.
3. Run the complete local quality gate:

```bash
python -m ruff check datamuru tests
python -m pytest
NO_MKDOCS_2_WARNING=1 python -m mkdocs build --strict
python -m build
python -m twine check dist/*
```

Use the `NO_MKDOCS_2_WARNING=1` environment variable only to suppress the
upstream Material for MkDocs informational banner about future MkDocs `2.0`
compatibility. DataMuru's docs dependency remains pinned to MkDocs `>=1.6,<2`.

4. Commit and push the release changes.
5. Confirm the **CI** and **Documentation** workflows pass.
6. Create a GitHub release whose tag exactly matches the package version with a `v` prefix, for example `v0.5.1a0`.
7. Publish the GitHub release.
8. Approve the `pypi` environment deployment if protection is enabled.
9. Verify `https://pypi.org/project/datamuru/`.
10. Test installation in a clean virtual environment:

```bash
python -m venv .venv-release-check
python -m pip install --upgrade pip
python -m pip install "datamuru==0.5.1a0"
datamuru --help
```

PyPI versions are immutable. If a release fails after publication, increment the version; do not attempt to overwrite the existing artifact.
