# Security and credentials

## Threat model

DataMuru runs with the permissions of its configured Databricks identity. A
compromised token or CI runner can perform every operation that identity can
perform.

Match controls to the supported surface in
[current capabilities and limits](../reference/capabilities-limits.md). Do not
grant privileges for roadmap resources that DataMuru cannot yet reconcile.

## Credential rules

- Store credentials in environment variables or a secret manager.
- Use separate credentials for development and production.
- Grant least privilege.
- Rotate credentials regularly and after any suspected exposure.
- Never place credentials in YAML, state, saved plans, examples, logs, or issue
  reports.

## Repository rules

- Ignore `.datamuru/`, virtual environments, build output, and local overrides.
- Use sanitized workspace URLs and resource names in public examples.
- Run secret scanning before every public release.
- Keep Enterprise implementation and customer runbooks in the private
  repository.

## Operational controls

- Protect the branch that publishes PyPI releases.
- Restrict access to the GitHub `pypi` environment.
- Review release tags before publication.
- Retain audit logs from GitHub, PyPI, and Databricks.
- Use saved plans and approvals for shared environments.
- Run `live-readonly` checks before any new `live-apply` workspace.
- Keep production credentials outside developer laptops when possible.

## Incident response

If a credential is exposed:

1. revoke or rotate it immediately;
2. inspect provider audit logs;
3. remove it from current files and Git history as required;
4. invalidate derived credentials;
5. document impact and corrective controls.
