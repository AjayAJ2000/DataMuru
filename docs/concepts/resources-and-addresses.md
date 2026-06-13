# Resources, addresses, and targets

Every compiled resource has a type, name, attributes, and stable address:

```text
<resource_type>:<name>
```

Examples:

```text
workspace:example-dev
catalog:analytics
schema:analytics.raw
group:data-consumers
permission_binding:data-consumers:curated_reader
```

Addresses identify plan entries, state records, and CLI targets.

Targets normally match one exact address. Two hierarchy rules expand targets:

- `catalog:<name>` also matches schemas in that catalog;
- `group:<name>` also matches memberships in that group.

Expansion makes common operations safer and more useful, but it is not a
general dependency graph. Always inspect the resulting plan.
