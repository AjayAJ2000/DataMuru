# Snowflake Programmatic Access Token Authentication Design

Status: implemented, pending milestone release

## Context

DataMuru supports Snowflake browser SSO and password environment variables for
live-readonly database and schema discovery. A Snowflake trial operator has
created a 30-day Programmatic Access Token and exposed it through
`SNOWFLAKE_HOST`, `SNOWFLAKE_TOKEN`, and `SNOWFLAKE_USERNAME`.

Snowflake Connector for Python 3.18.0 accepts
`PROGRAMMATIC_ACCESS_TOKEN` authentication. Live probes established two facts:

1. the connector requires an account identifier in addition to a host;
2. deriving the account label from the Snowflake hostname reaches Snowflake,
   where authentication is then subject to Snowflake's network-policy
   prerequisite for PATs.

DataMuru does not currently model Snowflake host or PAT token fields, so the
configured credentials cannot be used through the provider yet.

## Goals

- Add explicit Snowflake PAT authentication without generic connector-argument
  passthrough.
- Resolve host, token, and username from named environment variables.
- Accept a full Snowflake URL or hostname and normalize it in memory.
- Derive the connector account label from the normalized hostname only when
  `account` or `account_env` is not configured.
- Preserve existing external-browser and password authentication behavior.
- Keep PAT values out of configuration files, command output, diagnostics,
  state, plans, and generated artifacts.
- Validate the implementation with unit tests and live-readonly Snowflake
  identity and discovery probes.
- Commit and push each completed slice and require green CI, Documentation, and
  Documentation Links workflows.

## Non-goals

- No Snowflake live apply or destroy.
- No token generation, rotation, revocation, or storage.
- No OAuth implementation in this slice.
- No arbitrary connector keyword map.
- No automatic network-policy creation or modification.
- No credential values in logs, error contexts, or support bundles.
- No broad grant discovery or mutation.

## Provider Configuration

PAT configuration is explicit:

```yaml
provider:
  cloud: snowflake
  host_env: SNOWFLAKE_HOST
  user_env: SNOWFLAKE_USERNAME
  token_env: SNOWFLAKE_TOKEN
  auth_type: programmatic_access_token
  warehouse: COMPUTE_WH
  role: SYSADMIN
  execution_mode: live-readonly
```

Existing fields remain supported:

- `account` and `account_env` for an explicit Snowflake account identifier;
- `user` and `user_env` for a username;
- `password_env` for approved password-based sandbox authentication;
- `auth_type: externalbrowser` for interactive browser SSO.

`token_env` is used only by PAT authentication in this slice. DataMuru never
stores or returns the resolved token value.

## Host And Account Resolution

`host` and `host_env` accept either:

- `organization-account.snowflakecomputing.com`; or
- `https://organization-account.snowflakecomputing.com`.

Normalization removes the scheme, path, query, fragment, and trailing slash.
The connector receives the normalized hostname through `host`.

Account resolution order:

1. literal `account`;
2. value from `account_env`;
3. first DNS label from the normalized Snowflake hostname.

If no account or host can be resolved, live discovery fails before any network
call with a redacted configuration error. A malformed or non-Snowflake hostname
also fails locally rather than being guessed.

## Connector Behavior

For PAT mode, `SnowflakeSqlClient` passes only reviewed parameters:

```python
{
    "account": resolved_account,
    "host": normalized_host,
    "user": resolved_user,
    "authenticator": "PROGRAMMATIC_ACCESS_TOKEN",
    "token": resolved_token,
    "warehouse": configured_warehouse,
    "role": configured_role,
}
```

The `host`, `user`, `warehouse`, and `role` entries remain conditional when not
configured. PAT mode requires a token. Existing external-browser and password
paths continue to use their current connector arguments.

## Network Policy Boundary

Snowflake requires the PAT user to be subject to a network policy unless the
operator uses Snowflake's time-limited
`MINS_TO_BYPASS_NETWORK_POLICY_REQUIREMENT` option when creating a PAT. DataMuru
does not create policies or bypass this control.

The runbook must distinguish:

- recommended validation with an operator-managed network policy;
- a temporary trial-only bypass explicitly created in Snowflake;
- the expected `Network policy is required` failure when neither is present.

The temporary bypass does not bypass an existing network policy. Token
creation, rotation, and removal remain manual Snowflake administration tasks.

## Doctor And Errors

`doctor` adds redacted checks for:

- account or valid host availability;
- PAT token environment-variable availability;
- configured username posture;
- Snowflake connector availability;
- execution mode.

Checks may report the environment-variable name but never its value. Provider
errors must not include the token, host value, or username value. Connector
exceptions remain wrapped by the existing provider error boundary.

## Live-Readonly Validation

Live validation uses two non-mutating probes:

1. `SELECT CURRENT_ACCOUNT(), CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE()`;
2. bounded DataMuru database and schema discovery using `SHOW DATABASES` and
   `SHOW SCHEMAS IN DATABASE`.

Test output records only success state and whether returned identity fields are
present. It does not print account, host, username, role, warehouse, token, or
database contents unless the operator explicitly reviews a redacted artifact.

## Test Strategy

Use failing-first tests for:

1. resolving `host_env`, `token_env`, and `user_env`;
2. normalizing URL and hostname inputs;
3. explicit account precedence over host-derived account labels;
4. PAT connector arguments and uppercase authenticator;
5. missing-token failure before connector invocation;
6. doctor ready and blocked checks without token disclosure;
7. preservation of external-browser and password paths;
8. generated Snowflake starter configuration for PAT opt-in;
9. CLI validation and live-readonly discovery with no mutation;
10. full Ruff, pytest, documentation, and strict MkDocs gates.

## Documentation And Deployment

Update the Snowflake provider reference, authentication guide, CLI reference,
capability limits, changelog, and milestone test runbook. Document PAT creation
as an operator-owned Snowflake action and include network-policy and revocation
guidance.

After local verification:

1. commit the implementation to `main`;
2. push to GitHub;
3. wait for CI, Documentation, and Documentation Links workflows;
4. do not start the next implementation until all required workflows pass.

## Acceptance Criteria

- The three configured environment-variable names work without renaming them.
- A full Snowflake hostname yields a valid explicit connector account and host.
- PAT authentication reaches Snowflake; with the required network policy or
  approved temporary bypass, the identity query and discovery path complete.
- The network-policy prerequisite remains a Snowflake operator control.
- No credential value appears in output, errors, state, plans, tests, docs, or
  committed files.
- Existing Snowflake SSO and password tests remain green.
- Live mutation remains unavailable.
- The runbook contains exact PAT setup, identity-probe, discovery, redaction,
  network-policy, revocation, and bug-capture steps.
- All local and GitHub pipeline gates pass.
