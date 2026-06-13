# Plan and apply results

## Plan

A plan contains:

- `environment`;
- an ordered list of changes;
- each change's `action`, `resource`, `before`, `after`, and `reason`.

Actions are `create`, `update`, `noop`, and `destroy`.

## Apply

An apply result separates:

- successfully applied changes;
- resources that already matched;
- failures with resource addresses and provider errors.

Apply is not globally transactional. Successful parent-independent resources
may remain applied when another resource fails.

## JSON output

Use `--output json` where supported for diagnostics and automation. Treat output
contracts as alpha APIs: pin the package version and test parsers during
upgrades.
