# RBAC Model

Role-based access control is represented in the alpha through `governance/rbac.yml`.

## Current concepts

- Roles
- Permission declarations
- Role inheritance
- Principal assignments
- Domain scoping

## Compilation behavior

The alpha compiler converts:

- roles into `rbac_role` resources
- assignments into `permission_binding` resources

This gives the planning engine a stable way to include access intent in desired state calculations.

## Why this is useful now

Even before real provider enforcement exists, the RBAC model already provides:

- a stable config contract
- a testable planning surface
- a documentation surface for future contributors and customers
