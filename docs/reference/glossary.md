# Glossary

This glossary defines terms that have a specific meaning in DataMuru. Use these
terms consistently in configuration, output, and documentation.

## Apply

Execute the approved actions in a plan. An apply can create, update, or delete
resources when the provider and execution mode support those operations.

## Desired state

The resource definitions produced from DataMuru configuration for the selected
environment.

## Destroy

Plan and apply removal of managed resources. Destroy remains subject to target
selection, lifecycle rules, provider support, and explicit deletion safeguards.

## Execution mode

The provider operating level that determines whether DataMuru uses local state,
reads live resources, or performs live changes. See
[Choose an execution mode](../guides/execution-modes.md).

## Existing resource

A resource that DataMuru observes or references but does not own. Existing
resources should not be deleted by DataMuru.

## External resource

A resource that is outside DataMuru lifecycle management and is usually
identified through a reference or provider lookup.

## Managed resource

A resource whose lifecycle is controlled by DataMuru configuration, subject to
provider capabilities and deletion safeguards.

## Observed state

The resource state read from a provider or another supported source during
reconciliation.

## Permission binding

A compiled relationship between a principal, role, and governed resource. A
binding can produce one or more provider-specific grants.

## Plan

A deterministic comparison between desired state, stored state, and supported
observed state. A plan reports create, update, no-op, and delete actions without
performing them.

## Provider

The implementation that translates cloud-neutral DataMuru resources into
platform-specific reads and changes. The alpha provider targets Databricks.

## Resource address

The stable identifier DataMuru uses for a resource, such as
`catalog:analytics` or `schema:analytics.raw`.

## State

DataMuru's record of previously applied resource definitions and operation
metadata. State supports reconciliation; it is not a substitute for provider
discovery.

## Target

A resource address supplied to limit a plan, apply, or destroy operation.
DataMuru can include required related resources when target expansion applies.

## Taxonomy

A controlled set of classifications and governance metadata used to describe
data consistently.
