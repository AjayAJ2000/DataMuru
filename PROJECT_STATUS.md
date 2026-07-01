# DataMuru Project Status

Last updated: 2026-07-01

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

## Historical board snapshot

Total GitHub issues created/reused in the board setup: 69

- Open issues: 61
- Closed issues: 8
- Existing draft Project items retained: 10
- Total Project items: 78

## Count by status

These counts are the original board-setup snapshot from 2026-06-19, not current
delivery totals. Use live GitHub Project filters for current counts.

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
| M1 - Core Architecture | Provider, state, hosted control plane, and cross-provider handoff contracts exist; production backend decisions remain. |
| M2 - Backend and API Layer | Core CLI/API, resumable import, and remote-state boundaries exist; production remote state and multi-workspace planning remain. |
| M3 - Frontend and User Experience | CLI-first UX is the active surface; the previous local web UI is de-scoped pending a later enterprise-grade redesign. |
| M4 - Data Engineering and Governance | Databricks, basic governance, and bidirectional mapping drafts exist; metadata and live Snowflake governance remain. |
| M5 - Security, Access Control, and Compliance | Auth, RBAC, redacted audit evidence, and offline fulfillment exist; hosted signing and SCIM hardening remain. |
| M6 - Testing, QA, and Stabilization | Unit/e2e tests, CI, and manual live provider validation exist; performance and repeatable integration environments remain. |
| M7 - Deployment, Monitoring, and Release | PyPI, CI, docs, and release workflow exist; security scans, rollback, and monitoring strategy remain. |
| M8 - Documentation and Handover | Public docs exist; admin guide, demo script, handover, and maintenance guide remain. |

## Completed work summary

- Python package and CLI foundation.
- Clean source repository root with generated starter projects kept under
  `examples/` rather than tracked as top-level project state.
- Enterprise activation handoff package export for Cline, onboarding, and
  support review workflows.
- Offline Enterprise purchase approval/rejection evidence and activation
  receipts with deterministic fingerprints and conflict-safe writes.
- Resumable import checkpoints and structured progress evidence.
- Snowflake PAT authentication and live-readonly database/schema discovery.
- Review-only mappings in both Databricks-to-Snowflake directions.
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

- Actual payment processing, private package authorization, cryptographic
  license signing, hosted entitlement validation, and tenant provisioning need
  a future private Enterprise backend.
- Production remote state needs backend selection, locking, credentials, and
  hosted operating-model decisions.
- Snowflake grants import, RBAC mapping, and live mutation remain unimplemented.

## Top risks

1. Enterprise hosted control plane and private licensing scope is not finalized.
2. Remote state remains contract-only without production locking.
3. Snowflake live apply and governance parity trail Databricks.
4. Governance taxonomy and masking are not enforced live.
5. Alpha workflows still require manual review and controlled test accounts.
6. GitHub Project view layout still needs manual configuration because the CLI does not expose saved view editing.

## Next 10 recommended actions

1. Review the live GitHub Project and select a bounded v0.6 implementation slice.
2. Decide whether provider parity, governance enforcement, remote state, or
   identity hardening is the highest-value next outcome.
3. Define v0.6 acceptance criteria and a feature-by-feature runbook before code.
4. Keep enterprise web UI redesign behind CLI, provider, and security maturity.
5. Implement the selected metadata asset or governance expansion slice.
6. Harden Databricks account SCIM identity support.
7. Extend Snowflake grants discovery and RBAC mapping safely.
8. Design production remote state locking and recovery boundaries.
9. Evaluate a real DataMuru ASCII wordmark while preserving JSON and
   `--no-banner` automation behavior.
10. Keep hosted payment, signing, licensing, and provisioning in a private
    backend design track.

## Readiness

DataMuru remains an alpha. It is suitable for controlled evaluation, local
state workflows, scoped live-readonly discovery, supported Databricks changes,
and reviewable offline evidence. Production adoption still requires manual
approval controls, external secret management, independent audit retention,
provider-specific rollback procedures, and a production state backend.

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
