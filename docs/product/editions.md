# Editions and Commercial Model

DataMuru keeps its product boundary simple:

- `open-source`
- `enterprise`

## Runtime edition boundary

The code and configuration model should treat only these two editions as product-enforced boundaries.

### Open-source

Designed for:

- Individual developers
- Startup teams
- Early evaluators
- Contributors
- Single-workspace and mid-scale platform teams

### Enterprise

Designed for:

- Larger regulated organizations
- Multi-workspace platform teams
- Customers requiring richer reporting, policy automation, or support overlays
- Teams requiring hosted services, SSO/SAML, SIEM integrations, or SLA-backed support

## Commercial packaging

Commercial plans such as Startup and Business can exist as pricing and support offers, but they should not become separate runtime product modes in the codebase.

That distinction matters because it preserves:

- A clean configuration model
- A credible open-core boundary
- Predictable implementation behavior across deployments

## Repository implementation approach

The implementation approach is:

- this public repository owns the Apache-2.0 core, CLI, schemas, PyPI package, and documentation
- the private Enterprise repository depends on and extends released versions of the public core
- the configuration language and CLI contracts remain aligned across both editions
- Enterprise implementations are loaded through extension boundaries rather than copied into a long-lived fork

## Documentation stance

From a SaaS documentation perspective, this means product docs should:

- Explain edition differences clearly
- Avoid implying unsupported hidden tiers in the runtime
- Separate packaging, support, and deployment concerns cleanly
