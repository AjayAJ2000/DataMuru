# Getting Started Overview

This repository contains the first structured implementation slice of DataMuru. It is intentionally narrow, but it establishes the core shape of the framework.

## Alpha goals

The current alpha is designed to prove four things:

1. DataMuru can model a platform as configuration rather than scripts.
2. The framework can compute deterministic desired-state plans.
3. Provider-specific platform behavior can live behind a stable abstraction.
4. Governance concepts can be compiled early rather than bolted on later.

## What is included

- Root project configuration in `datamuru.yml`
- Environment, provider, workspace, and governance starter files
- Python package scaffold under `datamuru/`
- MkDocs-based documentation site under `docs/`
- JSON schema artifacts under `schemas/`
- Unit and end-to-end bootstrap tests under `tests/`

## What is intentionally out of scope

The alpha does not yet include:

- Brownfield import
- Cloud state backends beyond local state
- Full ABAC enforcement
- Ingestion, transformation, or observability engines
- Real Databricks API execution logic
- SaaS control plane features

## Recommended reader path

- Product or engineering leadership: read **Product > Platform Overview**
- Contributors: read **Architecture > Overview** and **Reference > CLI Reference**
- Evaluators: read **Installation** and **Quickstart**
