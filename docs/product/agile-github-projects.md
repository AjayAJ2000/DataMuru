# Agile planning with GitHub Projects

DataMuru should integrate with GitHub Projects instead of replacing it.
GitHub Projects already provides table, board, and roadmap views, custom
fields, charts, status updates, built-in automation, and API automation. That
makes it a strong free/low-friction agile layer for teams already using GitHub.

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
5. Pull project status back into the local UI so DataMuru shows delivery
   posture beside technical posture.

## First implementation target

The first implementation should be export-only:

```powershell
datamuru agile export --format github-issues --out .\github-issue-drafts
```

This avoids token and organization-permission complexity while still letting
teams review the generated agile backlog. After that, Enterprise can add
authenticated sync using a GitHub App or fine-grained token.
