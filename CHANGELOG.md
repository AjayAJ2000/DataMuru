# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project aims to follow Semantic Versioning.

## [Unreleased]

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
