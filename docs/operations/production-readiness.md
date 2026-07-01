# Production readiness

DataMuru `0.5.1a0` is not generally production-ready. Use this checklist to
decide whether a bounded pilot is acceptable.

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
