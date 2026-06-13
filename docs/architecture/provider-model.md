# Provider Model

DataMuru uses a provider abstraction to keep platform-specific behavior out of the core engine.

## Why the provider model matters

The framework needs to support:

- Multi-cloud evolution
- Platform-specific lifecycle behavior
- A stable orchestration core

Without a provider abstraction, those concerns would leak into every command and state transition.

## Current provider contract

The alpha provider interface includes:

- `authenticate`
- `build_desired_resources`
- `apply_resource`
- `destroy_resource`
- `get_resource_types`

## Current implementation

The active provider factory supports:

- `databricks`

The current Databricks provider:

- reads provider configuration
- validates the selected cloud family
- constructs desired resources from workspace declarations
- records local apply/destroy behavior

## Cloud strategy

The implementation is:

- Azure-first for the initial modeled experience
- Multi-cloud-aware in validation and interfaces
- intentionally not full-parity yet
