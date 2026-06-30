# Frequently asked questions

## Is DataMuru production-ready?

Not generally. `0.5.0a0` is an alpha release with real but bounded provider
support. Use the [production-readiness checklist](production-readiness.md)
before a pilot.

## Does DataMuru call real Databricks APIs?

Yes. Live modes can observe supported workspace resources. `live-apply` can
create and delete supported catalogs and schemas, apply supported Unity Catalog
grants, and perform enabled Enterprise identity operations where account SCIM
is available.

## Does `live-readonly` create resources?

No. It permits connectivity, observation, doctor checks, plans, and import
discovery but blocks provider mutations.

## Why did apply report zero changes?

The desired resources may already match live or local state. Run plan and check
whether entries are no-op. Also verify that the target matches a declared or
state-managed address.

## Why does default-storage catalog creation need a SQL warehouse?

DataMuru uses `CREATE CATALOG` through the SQL Statements API so Databricks can
choose account default storage. The direct Unity Catalog REST API can require an
explicit storage root.

## Does DataMuru replace Terraform?

DataMuru is a product-specific data platform and governance framework. It does
not aim to manage every cloud resource or replace a general infrastructure
tool.

## Can OSS manage users and groups?

OSS can reference existing principals for permissions. Managed account identity
lifecycle is an Enterprise capability and requires Databricks account SCIM.

## Where is state stored?

The OSS alpha implements local JSON state at the configured `state.path`. Cloud
backend names are reserved in the contract but are not implemented yet.

## Can I import an existing workspace?

You can discover supported resources and generate starter workspace YAML for
explicit review. Automatic broad ownership adoption is not yet available.
Explicit targeted import and adoption workflows are available where supported;
check [Current capabilities and limits](../reference/capabilities.md) before
using generated YAML as desired state.

## How do I report a problem?

Collect the DataMuru version, command, structured error code, and redacted
doctor output. Open a GitHub issue without secrets or private workspace data.
