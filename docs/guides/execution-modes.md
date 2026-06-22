# Choose an execution mode

Execution mode controls whether DataMuru contacts or changes Databricks.

| Mode | Contacts Databricks | Allows mutations | Use for |
| --- | --- | --- | --- |
| `state-only` | No | Local state only | learning, unit tests, configuration design |
| `live-readonly` | Yes | No | connectivity, discovery, drift-aware planning |
| `live-apply` | Yes | Supported resources | controlled integration tests and operations |

## Start in state-only

```yaml
execution_mode: state-only
```

Use this mode when credentials are unavailable or when designing configuration.
Provider diagnostics skip live connectivity.

## Move to live-readonly

```yaml
execution_mode: live-readonly
```

Run `doctor`, import discovery, and plan. Apply is blocked by the read-only
guard.

## Enable live-apply deliberately

```yaml
execution_mode: live-apply
```

Before applying:

1. confirm the workspace host;
2. run `validate` and `doctor`;
3. use a unique non-production target;
4. review the complete plan;
5. confirm required Databricks permissions;
6. retain a copy of state and the reviewed configuration.

Live apply does not mean every modeled resource has a live implementation. See
[Current capabilities and limits](../reference/capabilities-limits.md).
