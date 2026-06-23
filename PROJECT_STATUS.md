# DataMuru Project Status

Last updated: 2026-06-23

Project board: [DataMuru Product Roadmap](https://github.com/users/AjayAJ2000/projects/1)

## Project overview

DataMuru is a Python-first, provider-agnostic data infrastructure and governance
framework. The OSS package currently focuses on declarative configuration,
planning, local state, Databricks live operations, import discovery, basic
governance compilation, documentation, and PyPI distribution. The Enterprise
roadmap extends the OSS core with multi-workspace orchestration, deeper
identity/governance workflows, Snowflake parity, hosted review surfaces,
licensing, and operational evidence.

## Current delivery status

The GitHub Project has been converted into an execution board with lifecycle
milestones, labels, epics, actionable issues, completed evidence items, and
delivery metadata. The board should be treated as the source of truth for
planning and status; this file is the periodic written snapshot.

## Issue count

Total GitHub issues created/reused in the board setup: 69

- Open issues: 61
- Closed issues: 8
- Existing draft Project items retained: 10
- Total Project items: 78

## Count by status

These counts are delivery classifications based on repository evidence and the
board setup performed on 2026-06-19.

| Status | Count |
| --- | ---: |
| Backlog | 8 |
| To Do | 31 |
| In Progress | 7 |
| In Review | 10 |
| Blocked | 5 |
| Done | 8 |

## Count by module

| Module / area | Count |
| --- | ---: |
| Data Engineering | 16 |
| Docs | 15 |
| Governance | 12 |
| Backend / Core | 12 |
| Frontend / UI | 10 |
| Security | 8 |
| Testing | 8 |
| DevOps | 8 |
| Architecture | 6 |
| Release | 3 |

Some issues intentionally count toward more than one area because they cross
functional boundaries, such as security testing or governance documentation.

## Count by priority

| Priority | Count |
| --- | ---: |
| P0 - Critical | 3 |
| P1 - High | 48 |
| P2 - Medium | 17 |
| P3 - Low | 1 |

## Milestone progress

| Milestone | Current posture |
| --- | --- |
| M0 - Project Foundation | Product docs exist; personas, KPIs, decision log, and risk register need formalization. |
| M1 - Core Architecture | Architecture docs exist; hosted control plane and cross-provider mapping need design decisions. |
| M2 - Backend and API Layer | Core CLI/API exists; resumable import, remote state, and multi-workspace planner are next. |
| M3 - Frontend and User Experience | CLI-first UX is the active surface; the previous local web UI is de-scoped pending a later enterprise-grade redesign. |
| M4 - Data Engineering and Governance | Databricks and basic governance exist; metadata model, audit reporting, and Snowflake mapping remain. |
| M5 - Security, Access Control, and Compliance | Auth and RBAC basics exist; license, audit logging, SCIM hardening, and permission tests remain. |
| M6 - Testing, QA, and Stabilization | Unit/e2e tests and CI exist; live integration, performance, coverage, and manual enterprise QA remain. |
| M7 - Deployment, Monitoring, and Release | PyPI, CI, docs, and release workflow exist; security scans, rollback, and monitoring strategy remain. |
| M8 - Documentation and Handover | Public docs exist; admin guide, demo script, handover, and maintenance guide remain. |

## Completed work summary

- Python package and CLI foundation.
- Clean source repository root with generated starter projects kept under
  `examples/` rather than tracked as top-level project state.
- Enterprise activation handoff package export for Cline, onboarding, and
  support review workflows.
- Databricks catalog and schema live apply.
- Scoped import controls and grant guardrails.
- PyPI alpha release pipeline.
- GitHub Pages documentation pipeline.
- Branded CLI shell with script-friendly suppression.
- Governance taxonomy, RBAC, and masking compilers.
- CI, documentation, and package verification workflows.

## In-progress work summary

- CLI-first product experience and enterprise workflow polish.
- Core backend/API hardening.
- Governance engine expansion.
- Security and RBAC hardening.
- Documentation and handover expansion.
- Decision log and risk register maintenance.
- Databricks account SCIM identity support.

## Blocked work summary

- Hosted control plane architecture: initial OSS activation-readiness contract is now in progress.
- Enterprise license activation model: local preflight and redacted offline
  purchase request exports exist; actual license issuance and tenant
  provisioning remain blocked on Enterprise backend decisions.
- Databricks live integration tests: blocked on a dedicated test workspace.
- Snowflake trial integration tests: blocked on Snowflake trial credentials.
- Snowflake grants import and RBAC mapping: blocked on Snowflake live discovery and account access.

## Top risks

1. Large enterprise imports can run too long without resumable checkpoints.
2. Snowflake is not yet live-discovery or live-apply capable.
3. Enterprise hosted control plane scope is not finalized.
4. Security, audit, and license flows need clearer production contracts.
5. Live integration environments are required for trustworthy provider QA.
6. GitHub Project view layout still needs manual configuration because the CLI does not expose saved view editing.

## Next 10 recommended actions

1. Implement resumable import job checkpoint model.
2. Add import ETA, progress, and scan budget telemetry.
3. Add Databricks grant scan budgets by object type.
4. Keep enterprise web UI redesign in backlog until CLI-first workflows, import performance, provider parity, and security are stable.
5. Add remote state backend abstraction.
6. Implement metadata asset model.
7. Harden Databricks account SCIM identity support.
8. Create Databricks live integration test environment.
9. Create Snowflake trial validation environment.
10. Connect offline Enterprise activation contracts to a future hosted
    entitlement and tenant-provisioning backend.

## Readiness

MVP readiness: 42%

Production readiness: 18%

These percentages are qualitative delivery-health estimates. MVP readiness is
anchored on OSS package usefulness for local/alpha Databricks workflows.
Production readiness is lower because resumable imports, remote state, live
integration tests, audit evidence, security hardening, and Enterprise operating
model work remain.

## Board maintenance instructions

- Keep real GitHub issues as the source of truth; avoid using draft Project
  items for new work unless the item is intentionally not ready for an issue.
- Every new issue should include acceptance criteria, codebase area, milestone,
  labels, risk, and a clear dependency/blocker statement.
- Use `Delivery Status` for the exact lifecycle status: `Backlog`, `To Do`,
  `In Progress`, `In Review`, `Blocked`, or `Done`.
- Use the built-in GitHub `Status` field for visual board grouping where
  useful, but rely on `Delivery Status` for TPM reporting.
- Move work to `Done` only when repository evidence exists.
- Update this file after major board changes, release tags, or milestone
  planning sessions.
