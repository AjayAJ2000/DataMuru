# Target related resources

Targets reduce the plan or operation to one resource address and selected
dependencies.

## Target an exact resource

```powershell
datamuru plan --target schema:analytics.raw
```

## Target a catalog and its schemas

```powershell
datamuru plan --target catalog:analytics
```

A catalog target also matches addresses beginning with
`schema:analytics.`.

## Target a group and memberships

```powershell
datamuru plan --target group:data-consumers
```

A group target also matches addresses beginning with
`group_membership:data-consumers:`.

## Use complete addresses

Examples:

```text
catalog:analytics
schema:analytics.raw
permission_binding:data-consumers:catalog_reader
group_membership:data-consumers:user:analyst@company.com
```

If a target matches neither desired configuration nor local state, DataMuru
reports that no matching resource was found. It should not be interpreted as a
successful apply.

Targets are a safety aid, not a dependency solver for every resource type.
