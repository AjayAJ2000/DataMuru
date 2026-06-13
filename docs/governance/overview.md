# Governance Overview

Governance is central to the product identity of DataMuru. Even in the alpha, governance is modeled as a first-class part of the desired state.

## Included in the current alpha

- Taxonomy compilation
- RBAC compilation
- Masking compilation

## Why this matters early

Starting governance in the bootstrap gives the framework three advantages:

1. Governance concepts become part of the data model, not a post-hoc extension.
2. Provider and plan logic can evolve with governance in mind.
3. Documentation and schemas can establish the language of control early.

## Current limitation

The alpha compiles governance concepts into internal resources, but it does not yet enforce them against a live Databricks control surface. That will come later as provider execution matures.
