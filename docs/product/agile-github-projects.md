# Agile planning with GitHub Projects

DataMuru should integrate with GitHub Projects instead of replacing it.
GitHub Projects already provides table, board, and roadmap views, custom
fields, charts, status updates, built-in automation, and API automation. That
makes it a strong free/low-friction agile layer for teams already using GitHub.

The product principle is simple: GitHub Projects tracks delivery work;
DataMuru produces platform evidence. Do not make DataMuru a project management
system. Make it useful to the project management system.

## Product fit

Use GitHub Projects for:

- roadmap epics;
- provider milestones;
- enterprise onboarding tasks;
- customer feedback triage;
- release readiness;
- documentation and testing work.

Use DataMuru for:

- platform inventory;
- governance declarations;
- provider diagnostics;
- plan/apply evidence;
- import review artifacts.

The integration boundary is simple: DataMuru produces structured work items and
evidence; GitHub Projects tracks ownership, priority, sprint/iteration, status,
and delivery.

## Enterprise operating model

Use one private user-level or organization-level project for DataMuru product
execution. Use public OSS issues only for community-facing bugs, enhancements,
and docs feedback.

Recommended split:

| Work type | Location |
| --- | --- |
| OSS bug reports | Public GitHub issues |
| OSS feature requests | Public GitHub issues |
| Enterprise roadmap | Private GitHub Project |
| Customer feedback | Private GitHub Project |
| Security-sensitive findings | Private security advisory or private issue |
| Release tracking | Private GitHub Project plus public release notes |

This keeps community collaboration open while protecting commercial roadmap,
customer details, and enterprise testing context.

## Recommended fields

Create these GitHub Project fields:

| Field | Type | Purpose |
| --- | --- | --- |
| Area | Single select | OSS, Enterprise, Docs, Provider, Governance, UI |
| Provider | Single select | Databricks, Snowflake, AWS, Azure, GCP |
| Edition | Single select | OSS, Enterprise |
| Customer impact | Single select | Evaluation, Production, Security, Cost |
| Risk | Single select | Low, Medium, High |
| Release target | Text | Package or milestone target |
| Evidence link | Text | Plan, docs, CI, or issue evidence |

## Integration roadmap

1. Generate local issue drafts from DataMuru roadmap and validation output.
2. Sync issue drafts to GitHub Issues with labels and milestone hints.
3. Add created issues to a GitHub Project through the GraphQL API.
4. Update custom fields such as Area, Provider, Risk, and Release target.
5. Pull project status into CLI evidence reports first, then revisit a
   dedicated enterprise UI after the core workflows are stable.

## First implementation target

The first implementation should be export-only:

```powershell
datamuru agile export --format github-issues --out .\github-issue-drafts
```

This avoids token and organization-permission complexity while still letting
teams review the generated agile backlog. After that, Enterprise can add
authenticated sync using a GitHub App or fine-grained token.

The export writes:

- one Markdown issue draft per backlog row;
- front matter with title, labels, and release target;
- planning fields for area, provider, edition, impact, and risk;
- a `manifest.json` file that lists every generated draft.

Scope one milestone at a time:

```powershell
datamuru agile export `
  --format github-issues `
  --release-target 0.5.1a0 `
  --out .\github-issue-drafts\0.5.1a0
```

Review the generated Markdown before creating public issues. Enterprise-only,
customer-specific, and security-sensitive items should stay in a private
project or private repository.

## Recommended board

Use the board design in [Recommended GitHub Project board](github-project-board.md)
as the starting point for the private product roadmap.

## Why this works

GitHub Projects is already close to how engineering teams work: issues,
pull requests, milestones, boards, roadmaps, and automation live together. The
DataMuru value is not duplicating that surface. The value is generating better
work items from real platform state:

- import discovered too many unmanaged catalogs;
- RBAC grants differ between environments;
- a provider is missing SSO or warehouse configuration;
- a plan has pending destructive changes;
- a release needs docs, tests, and PyPI validation.

Those findings should become trackable work with evidence links.
