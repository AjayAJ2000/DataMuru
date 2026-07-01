# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project aims to follow Semantic Versioning.

## [Unreleased]

## [0.5.1a0] - 2026-07-01

### Added
- Added `datamuru enterprise activation fulfill` for validated offline approval/rejection evidence with deterministic request and decision fingerprints plus stable decision and receipt IDs.
- Added conflict-safe fulfillment writers, a config-independent Python API, redacted error handling, and milestone runbook coverage for tamper and leakage testing.

## [0.5.0a0] - 2026-06-30

### Added
- Added `datamuru import map-databricks` for review-only Snowflake-to-Databricks database and schema mapping drafts with collision checks.
- Added explicit Snowflake Programmatic Access Token authentication for redacted live-readonly database and schema discovery.
- Added `datamuru enterprise activation check` for local hosted-control-plane and license activation readiness preflight.
- Added `datamuru enterprise activation export` for redacted activation handoff bundle generation.
- Added `datamuru enterprise activation purchase-request` for redacted offline purchase and license activation handoff packages.
- Added `datamuru enterprise activation evidence` for redacted audit evidence export.
- Added `datamuru enterprise activation package` for a single redacted onboarding directory with activation, purchase, evidence, control-plane, architecture, tenant entitlement, and manifest artifacts.
- Added `datamuru enterprise control-plane tenant-record` for deterministic, redacted, offline tenant entitlement handoff records.
- Added `datamuru enterprise control-plane architecture` for hosted control plane reference architecture export.
- Added the `enterprise.activation` root configuration contract and docs for redacted Enterprise onboarding payloads.
- Added `datamuru enterprise control-plane contract` for redacted hosted control plane handoff contracts.
- Added `datamuru state inspect` for local and remote state backend readiness checks.
- Added an explicit `DMR-STATE-REMOTE` planning boundary for recognized remote state contracts in the OSS runtime.
- Added a milestone 0.5 test runbook for feature-by-feature activation readiness validation.

### Fixed
- Fixed resumable import job checkpoints so the `updated_at` timestamp written by `--job-checkpoint` can be read back by `--resume-from`.
- Fixed `datamuru init --provider snowflake` so generated provider, environment, workspace, README, and default cloud values use Snowflake settings instead of Databricks defaults.

## [0.4.0a0] - 2026-06-20

### Added
- Added enterprise import suite file naming with `--suite-layout enterprise` and `--suite-prefix`.
- Added validation warnings for enterprise file naming conventions.
- Added per-object grant scan budgets for Databricks import discovery with `--max-catalog-grant-objects` and `--max-schema-grant-objects`.
- Added structured import progress events and `--progress-checkpoint` for long-running discovery and generation workflows.
- Added resumable import grant-scan checkpoints with `--job-checkpoint` and `--resume-from`.
- Added Snowflake live-readonly database and schema discovery with the `datamuru[snowflake]` extra.
- Added `datamuru import map-snowflake` for draft Databricks-to-Snowflake catalog/schema mapping contracts.
- Added `datamuru agile export` for local GitHub issue draft generation from the roadmap table.
- Added a milestone 0.4 test runbook for feature-by-feature validation and bug capture.

### Changed
- Increased DataMuru logo presence in the README and documentation site.

## [0.3.7a0] - 2026-06-20

### Added
- Added a branded CLI shell header for interactive DataMuru commands.
- Added `--no-banner` for automation that needs clean command output.

### Changed
- Removed the experimental local web UI from the public CLI surface until it can be redesigned as an enterprise-grade experience.
- Updated enterprise testing and import documentation to use CLI-first review flows.

## [0.3.6a0] - 2026-06-19

### Added
- Reworked `datamuru ui` into a more enterprise-oriented local console with project posture, workspace visibility, feature posture, validation readiness, and rollout guidance.
- Added enterprise project structure guidance with naming conventions for providers, environments, workspaces, imports, governance, and migrations.
- Added Databricks-to-Snowflake adoption guidance for staged inventory, review-suite generation, and Snowflake trial planning.
- Added a recommended private GitHub Project board model for DataMuru roadmap execution.

### Changed
- Expanded Snowflake provider docs from scaffold-only reference to a practical evaluation path with clear live-execution limits.

## [0.3.5a0] - 2026-06-19

### Changed
- Slimmed the test extra to dependencies used by the current test suite to reduce Python-version plugin drift in CI.
- DataMuru now declares Python 3.11 through 3.13 support while Python 3.10 compatibility is investigated.

## [0.3.4a0] - 2026-06-19

### Added
- `datamuru import discover` and `datamuru import generate` now support `--grant-scope catalog|schema|all`.
- Import grant discovery now has `--max-grant-objects` to stop expensive scans before SQL warehouse work starts.
- Added `datamuru ui`, a local web dashboard for configuration health and declared resource inventory without live provider scans.
- Added GitHub Projects agile planning guidance for roadmap, feedback, release, and enterprise onboarding workflows.

### Changed
- Grant discovery defaults to catalog-level scanning for safer enterprise imports.
- Enterprise import docs now recommend inventory-first, scoped catalog scans before full schema grant discovery.

## [0.3.3a0] - 2026-06-18

### Added
- Import discovery now shows interactive progress for text output, including the current Databricks provider stage.
- `datamuru import discover` now supports repeated `--catalog` filters to scope catalog, schema, and grant discovery.
- Python import APIs accept an optional progress callback for product integrations.

### Changed
- Enterprise import documentation now explains why grant discovery can take longer and recommends scoped discovery before broad scans.

## [0.3.2a0] - 2026-06-18

### Fixed
- Databricks CLI profile authentication now uses Databricks SDK unified auth headers so SSO/OAuth profiles work the same way as `databricks catalogs list --profile <profile>`.
- `doctor` no longer requires a static token inside `.databrickscfg` for Databricks CLI profile auth.

## [0.3.1a0] - 2026-06-18

### Fixed
- Databricks enterprise connectivity checks now fall back to Unity Catalog when the SCIM `/Me` endpoint returns `403`.

## [0.3.0a0] - 2026-06-18

### Added
- Databricks CLI profile authentication using `.databrickscfg`, `DATABRICKS_CONFIG_FILE`, and `DATABRICKS_CONFIG_PROFILE`.
- Enterprise import suite generation for workspace, RBAC, taxonomy, and masking review files.
- Import discovery options for identity context and Unity Catalog grants.
- Snowflake provider scaffold for state-only planning of database/schema resources.
- OSS-to-Enterprise migration guide, Snowflake provider reference, AI discovery page, and `llms.txt`.
- Landing page AI SEO metadata, structured software schema, and `llms.txt` route.

### Changed
- Databricks raw HTTP operations now accept bearer tokens from PAT, CLI profile, or OAuth token sources.
- Enterprise testing docs now cover CLI profile auth, import suite review, and staged enterprise validation.
- Landing copy now describes Databricks as live alpha and Snowflake as a state-only scaffold.

## [0.2.0a0] - 2026-06-17

### Added
- Saved-plan metadata, schema versioning, and stale-configuration checks.
- Richer cross-file validation for environments, provider/cloud consistency, catalogs, schemas, and RBAC references.
- Structured apply failure metadata for provider errors and dependency skips.
- Environment-based Databricks starter configuration with generated `.env.example`.
- Improved `datamuru init` scaffolding with safer default catalog names and starter README output.

### Changed
- Starter Databricks provider configuration now uses `host_env`, `token_env`, and `sql_warehouse_id_env`.
- Public docs and schemas now reflect the stricter v0.2 validation behavior.
- DataMuru logo usage is enlarged across README, documentation, and landing surfaces.

### Added
- Product-grade documentation organized into tutorials, task guides, concepts, references, operations, and contributor guidance
- Complete operator documentation for authentication, execution modes, planning, saved plans, targeting, import, ACLs, destruction, and troubleshooting
- Reference pages for configuration, provider fields, environment variables, resource addresses, result contracts, error codes, and current capability limits
- Automated tests for MkDocs navigation targets and relative Markdown links
- Documentation style guide based on Google technical-writing principles
- Documentation governance based on Write the Docs principles, including
  ownership, maintenance, feedback, review, accessibility, and terminology
- Scheduled external-link validation and expanded documentation contract tests
- Structured GitHub issue forms and a documentation-aware pull request template
- Git-backed page revision metadata and a product glossary
- Shared-core OSS and Enterprise track scaffolding
- MkDocs-based product documentation
- Databricks Free Edition setup guidance
- Edition-aware validation
- CLI doctor and edition inspection flows
- Saved-plan apply support
- Databricks account SCIM capability discovery
- Enterprise users, groups, service principals, and group membership lifecycle
- Identity drift observation with conservative deletion safeguards
- Runtime identity capability detection that takes precedence over edition assumptions
- Complete runnable OSS example project
- GitHub Actions CI across Python 3.10 through 3.13
- GitHub Pages documentation deployment
- OIDC-based PyPI Trusted Publishing workflow
- Contributor and security policies

### Changed
- PyPI-oriented package metadata expanded
- CLI output foundation moved toward rich-themed product output
- Legacy string principals now behave as existing references instead of managed lifecycle resources
- Target selection now uses explicit catalog/schema and group/membership relationships
- Identity validation now rejects misplaced principal blocks and reserved example-domain managed users
- Targeted plan and apply commands now explain when no declared or state-managed resource matched
- Package metadata now targets public PyPI distribution and GitHub Pages documentation
- Unused runtime dependencies were removed to reduce install size and dependency risk
