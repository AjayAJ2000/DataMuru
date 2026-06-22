# Production readiness

DataMuru `0.4.0a0` is an alpha release. It is useful for local evaluation,
safe planning, read-only provider checks, and narrow non-production pilots, but
it is not a drop-in production control plane.

Use the [current capabilities and limits](../reference/capabilities-limits.md)
page as the canonical status reference before approving any rollout.

## Safe alpha use

These workflows are reasonable for alpha evaluation when credentials are
scoped and state is backed up:

- initializing projects with `datamuru init`;
- validating configuration with `datamuru validate --strict`;
- planning changes in `state-only` or `live-readonly` mode;
- applying local `state-only` changes to learn reconciliation behavior;
- running `datamuru doctor` against a non-production Databricks workspace;
- discovering supported Databricks catalogs, schemas, grants, and jobs in
  `live-readonly` mode;
- testing narrowly targeted catalog, schema, and grant changes in a sandbox.

## Requires manual review

Require a human review before:

- any `live-apply` run;
- any destroy plan;
- any generated import or adoption YAML;
- any permission binding that affects shared groups or service principals;
- any Enterprise activation evidence or control-plane export before sharing it;
- any workflow that depends on unsupported resources or roadmap capabilities.

Review the plan output, target resources, execution mode, state location, and
rollback notes together. Do not rely on `--auto-approve` as a team control.

## Not production-ready yet

Do not depend on DataMuru OSS `0.4.0a0` for:

- production cloud state backends or state locking;
- broad multi-workspace orchestration;
- complete Databricks object coverage;
- live taxonomy, masking, or column policy enforcement;
- transactional rollback across provider operations;
- unattended production applies without an external approval process;
- Terraform replacement for all managed resources.

## Required before a pilot

- supported resources match the intended use case;
- non-production integration tests pass;
- credentials follow least privilege;
- state is backed up and concurrency is controlled;
- every destroy path has been tested;
- Databricks quotas and permissions are understood;
- monitoring covers GitHub Actions, provider errors, and Databricks audit logs;
- an operator owns rollback and incident response.

## Known alpha risks

- local state has no locking;
- apply is not globally transactional;
- provider coverage is incomplete;
- output and Python contracts may change;
- multi-cloud behavior is not at parity;
- generated import configuration needs human review;
- no SLA is provided for OSS.

## Recommended rollout

1. local state-only evaluation;
2. read-only development workspace;
3. unique live test resources;
4. narrow team pilot;
5. production only after a formal risk review.

Enterprise teams should add branch protection, saved-plan approvals, secret
scanning, audit-log retention, change tickets, and workspace-specific
least-privilege identities before expanding beyond sandbox resources.
