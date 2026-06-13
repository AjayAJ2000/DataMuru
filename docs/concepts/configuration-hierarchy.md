# Configuration hierarchy

DataMuru uses separate files to keep concerns reviewable.

1. `datamuru.yml` selects project-level contracts.
2. `environments/*.yml` carries environment metadata.
3. `providers/*.yml` configures provider connectivity and execution.
4. `workspaces/*.yml` declares resources and principals.
5. `governance/*.yml` declares taxonomy, roles, assignments, and masks.

Paths are resolved from the directory containing `datamuru.yml`.

The alpha loads the configuration for `default_environment`. The Python API
accepts an environment argument, but project loading and file selection remain
intentionally conservative while richer overlays are developed.

Keep environment-specific credentials outside YAML. Use environment variables
or a secret manager.
