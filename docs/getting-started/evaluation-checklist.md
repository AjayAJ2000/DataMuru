# Evaluation Checklist

Use this checklist when deciding whether DataMuru is ready for your team,
workspace, or enterprise pilot. It separates product fit, technical readiness,
and operational risk so evaluation does not collapse into a single demo.

## 1. Confirm the evaluation goal

Choose one primary goal for the first test:

- **Local workflow evaluation:** validate configuration, plans, state, saved
  plans, and CLI behavior without cloud access.
- **Databricks workspace smoke test:** connect a workspace and create a small
  catalog/schema target.
- **Governance smoke test:** compile RBAC into Unity Catalog grants for an
  existing principal.
- **Brownfield review:** discover existing catalogs and generate reviewable
  YAML.
- **Enterprise identity pilot:** test managed groups or memberships in a
  sandbox account with account SCIM support.

Avoid testing every capability in one first run. A focused test produces
clearer evidence and safer cleanup.

## 2. Prepare the environment

| Area | Required decision |
| --- | --- |
| Python | Use Python 3.10 through 3.13. |
| Package | Install a pinned alpha version such as `datamuru==0.3.1a0`. |
| Workspace | Use a sandbox Databricks workspace or a throwaway catalog. |
| Credentials | Use environment variables, not committed YAML. |
| State | Start with local state until the workflow is understood. |
| Execution mode | Start in `state-only` or `live-readonly`; use `live-apply` only for reviewed targets. |

## 3. Minimum success criteria

A healthy first evaluation should produce:

- `datamuru validate --strict` succeeds;
- `datamuru doctor` reports a reachable workspace in live modes;
- `datamuru plan --target ...` contains only expected resources;
- `datamuru apply --target ... --auto-approve` succeeds for the test target;
- a follow-up plan is idempotent;
- errors, if any, include a DataMuru error code and actionable suggestion;
- cleanup instructions are known before live resources are created.

## 4. Evidence to capture

Keep a small evidence folder for the evaluation:

- package version and install command;
- sanitized provider config;
- sanitized `doctor --output json`;
- targeted plan output;
- apply output;
- follow-up idempotent plan output;
- cleanup or destroy result;
- gaps found and whether they are OSS, Enterprise, Databricks, or process gaps.

Do not store tokens, private workspace URLs, customer data, or full account IDs.

## 5. Decision outcomes

At the end of evaluation, classify the result:

- **Proceed:** the tested flow is safe enough for a larger sandbox pilot.
- **Proceed with constraints:** the flow works, but requires documented
  guardrails, permissions, or account features.
- **Defer:** a required capability is still roadmap or needs Enterprise support.
- **Do not use for this workflow yet:** the workflow requires unsupported
  provider behavior, transactional rollback, or production state backends.

Document the decision next to the test evidence so the next team does not
repeat the same discovery work.
