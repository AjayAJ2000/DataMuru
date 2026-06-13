# FAQ

## Is DataMuru production-ready today?

Not yet. This repository currently represents an alpha bootstrap intended to establish architecture, interfaces, tests, and documentation patterns.

## Does the current provider call real Databricks APIs?

No. The current provider models desired resources and local orchestration behavior. Live provider mutations are a later phase.

## Why document so much at alpha stage?

Because DataMuru is intended to become an enterprise-facing platform product. Documentation quality is part of product quality, not a later marketing exercise.

## Why MkDocs?

MkDocs provides a clean path to maintainable, versionable, documentation-as-code workflows that fit a product engineering repository well.

## Why is the cloud strategy Azure-first but multi-cloud-aware?

Because the implementation needs one concrete end-to-end target first, while the architecture still needs to preserve the future for AWS and GCP.
