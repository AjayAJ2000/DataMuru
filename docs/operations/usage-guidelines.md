# Product Usage Guidelines

These guidelines describe how teams should use DataMuru as a product, not just as a source repository.

## Treat configuration as a reviewed contract

- Keep `datamuru.yml` and related config files under version control.
- Review changes through pull requests.
- Avoid editing environment intent directly in deployed state files.

## Use plans as approval artifacts

- Run `datamuru plan` before `apply`.
- Save plans for reviewable changes when operating in shared environments.
- Treat a saved plan file as a deployment artifact, not just terminal output.

## Keep edition boundaries explicit

- Use `open-source` for OSS-compatible footprints.
- Use `enterprise` only when you intentionally need enterprise-only features.
- Avoid "soft-enterprise" drift where OSS config quietly accumulates paid-only assumptions.

## Prefer productized onboarding over tribal knowledge

- Point teams to the documentation site first.
- Keep setup instructions current for the package distribution path.
- Keep examples aligned with the actual CLI and schema behavior.

## Standard operator flow

- Run `validate` before every shared change.
- Run `doctor` before onboarding a new workstation or CI runner.
- Review a `plan` before `apply`.
- Keep saved plans for auditable environment changes.
- Treat state files as system artifacts, not hand-edited configuration.

## Respect stage reality

At the current alpha stage:

- local workflow validation is real
- product structure is real
- live Databricks mutation coverage is still evolving

Teams should adopt the framework with that expectation and avoid presenting the current alpha as full production automation.
