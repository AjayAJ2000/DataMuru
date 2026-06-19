# Choose a starting path

Choose the shortest path that matches what you need to learn. You do not need
Databricks access to evaluate configuration, planning, state, or the CLI.

## Before you begin

You need:

- Python 3.11 through 3.13;
- a terminal with permission to create a virtual environment;
- Git only if you plan to contribute or use repository examples.

For live Databricks work, you also need:

- a workspace URL;
- a personal access token or another configured authentication method;
- permissions for the objects you plan to read or change;
- a SQL warehouse ID when using default-storage catalog creation or live ACLs.

## Select your path

### I want a safe local evaluation

Follow the [five-minute local quickstart](quickstart.md). It uses `state-only`
mode and does not contact Databricks.

You will learn how to validate a complete project, read a plan, apply changes to
local state, and verify idempotency.

### I have a Databricks workspace

Follow [Connect a Databricks workspace](../tutorials/connect-databricks.md).
Start in `live-readonly` mode. This verifies credentials and discovers supported
objects without allowing mutations.

### I use Databricks Free Edition

Read [Databricks Free Edition](databricks-free-edition.md) before enabling live
apply. Free Edition has product and account-level limitations that affect
identity and workspace administration.

### I already have catalogs and schemas

Use the [import tutorial](../tutorials/import-existing-workspace.md). Discovery
is read-only. Generated YAML is a review artifact and does not automatically
adopt or mutate every discovered object.

### I am integrating DataMuru into a team workflow

Read:

- [Operating model](../operations/usage-guidelines.md)
- [Team adoption](../operations/team-adoption-guidelines.md)
- [Security and credentials](../operations/security.md)
- [Production readiness](../operations/production-readiness.md)

## Understand the alpha boundary

DataMuru performs real live operations for selected resources. It does not yet
implement the complete PRD. Before each test, check
[Current capabilities and limits](../reference/capabilities.md).
