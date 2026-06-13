# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project aims to follow Semantic Versioning.

## [Unreleased]

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
