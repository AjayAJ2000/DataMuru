# Release Roadmap

The roadmap in this repository is implementation-oriented and grounded in the current scaffold.

The next product move is to grow the shared core while building the OSS and Enterprise tracks in parallel without splitting the codebase.

## v0.1 Alpha

Focus:

- Foundation layer bootstrap
- Local state backend
- Deterministic plan/apply/destroy workflow
- Azure-first Databricks provider abstraction
- Basic governance compilation
- CLI bootstrap
- Product-grade documentation baseline

## Next likely milestones

### v0.2

- Saved-plan apply hardening with metadata and stale-config checks
- Richer schema validation
- Better error modeling
- More complete starter project scaffolding
- OSS and Enterprise track maturation around shared edition-aware contracts

### v0.3

- Databricks CLI profile authentication and enterprise auth-extension boundary
- Brownfield import suite generation for workspace, RBAC, taxonomy, and masking review
- Identity and grant-aware import discovery where account SCIM and SQL warehouse access are available
- Snowflake provider scaffold for state-only planning
- Stronger provider contract coverage

### v1.0 target direction

- Complete open-source surface for the initial provider
- More production-grade provider execution logic
- Broader governance enforcement support
- More polished contributor and operator workflows

## Documentation implication

Every roadmap stage should ship with matching docs updates. For an international SaaS product, stale docs are a product defect, not a documentation inconvenience.
