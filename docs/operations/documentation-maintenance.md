# Maintain the documentation

Documentation is part of the DataMuru product and follows the same version
control, review, testing, and release workflow as code.

## Ownership

`CODEOWNERS` assigns review responsibility for documentation, schemas, examples,
CLI contracts, and provider behavior. Ownership does not prevent contributions;
it ensures that changes reach an appropriate reviewer.

## Update documentation with product changes

A pull request must update documentation when it changes:

- CLI commands or options;
- configuration fields or validation behavior;
- supported resource types or addresses;
- provider capabilities, permissions, or limitations;
- install, upgrade, security, or troubleshooting workflows;
- edition boundaries.

If no documentation change is needed, the pull request should explain why.

## Review cadence

- Review affected pages in every product pull request.
- Review installation, quickstart, capability, security, and troubleshooting
  pages for every release.
- Run a complete content audit at least every six months.
- Triage broken-link reports and reader feedback as product defects.

The site displays revision metadata derived from Git history. A recent date
does not guarantee accuracy, so reviewers must still validate content against
the implementation.

## Content lifecycle

Each page should be in one of these states:

- **Current:** matches a supported release.
- **Preview:** describes an unreleased feature and is marked clearly.
- **Deprecated:** still relevant to supported users but points to a replacement.
- **Removed:** deleted from navigation and redirected when practical.

Do not leave obsolete instructions in place merely to preserve page count.

## Versioning policy

The current site documents the latest OSS release and unreleased `main` branch
where explicitly stated. During the `0.x` phase:

- pin package versions in tutorials when reproducibility matters;
- mark unreleased behavior clearly;
- retain release notes and changelog history;
- test documentation before publishing a release;
- introduce versioned documentation before supporting multiple incompatible
  production release lines.

## Quality gates

Required checks:

```powershell
python -m pytest -q
python -m ruff check datamuru tests
python -m mkdocs build --strict
```

CI also validates navigation, internal links, document structure, source
references, and scheduled external links.
