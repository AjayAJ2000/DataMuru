# Governance configuration

## Taxonomy

`governance/taxonomy.yml` contains a taxonomy name, version, and unique category
IDs. Categories may include labels, descriptions, parents, and handling
metadata.

## RBAC

`governance/rbac.yml` contains:

- `roles`: reusable permission sets;
- `assignments`: principal-to-role bindings;
- `domains`: catalog scopes used to expand patterns.

Live ACL support currently accepts catalog and schema permissions.

## Masking

`governance/masking.yml` declares built-in mask IDs, descriptions, and
strategies. The alpha compiles masking resources as local governance intent;
live column-mask installation is not yet implemented.

See the [RBAC model](../governance/rbac.md) and
[capability reference](capabilities-limits.md).
