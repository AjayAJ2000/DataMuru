# Prepare Enterprise activation

Enterprise activation is the handoff between a local DataMuru project and a
hosted Enterprise control plane. The OSS CLI does not call a license server, but
it can verify that the project contains the fields an Enterprise onboarding
workflow needs.

## Configure activation intent

Use `project.edition: enterprise`, enable the hosted control plane feature, and
add an `enterprise.activation` block:

```yaml
project:
  edition: enterprise

features:
  hosted_control_plane: true
  identity_management: true

enterprise:
  activation:
    organization: Acme Data
    contact_email: platform@acme.example
    control_plane_url: https://control.datamuru.example
    tenant_id: acme-prod
    deployment_region: us-east-1
    license_key_env: DATAMURU_LICENSE_KEY
    purchase_reference: PO-12345
    support_plan: enterprise
```

`license_key_env` names the environment variable that contains the license key.
The CLI only reports whether the variable exists; it does not print the secret.

## Run the preflight

```powershell
$env:DATAMURU_LICENSE_KEY="<issued-license-key>"
datamuru enterprise activation check --config datamuru.yml
```

For automation:

```powershell
datamuru --no-banner enterprise activation check `
  --config datamuru.yml `
  --output json
```

The JSON payload is safe to attach to an onboarding ticket because it redacts
the license key value and includes only `license_key_present`.

## Export a handoff bundle

When the preflight is ready, write a redacted activation bundle:

```powershell
datamuru enterprise activation export `
  --config datamuru.yml `
  --out .\.datamuru\activation\enterprise-activation.json
```

The bundle contains:

- the activation report;
- the redacted onboarding payload;
- the readiness status;
- follow-up notes for entitlement, tenant provisioning, control plane binding,
  and evidence capture.

The bundle does not contain the license key value. If activation is blocked,
the command exits without writing a file. Use `--allow-blocked` only when a
support engineer asks for a diagnostic bundle with failed checks.

## Export a purchase and license request

To start commercial entitlement, tenant provisioning, or support review without
calling a license server, write a redacted purchase request:

```powershell
datamuru enterprise activation purchase-request `
  --config datamuru.yml `
  --out .\.datamuru\activation\purchase-request.json `
  --output json
```

The request includes:

- organization and contact metadata;
- purchase reference and support plan;
- requested Enterprise entitlements based on enabled features;
- tenant id, deployment region, and control plane URL;
- license key environment-variable name and presence status;
- confirmation that the command is offline and does not provision a tenant.

It does not contain the license key value. If activation is blocked, the command
does not write a file unless `--allow-blocked` is supplied for support triage.

## Export audit evidence

Generate a redacted evidence report for an onboarding, audit, or support ticket:

```powershell
datamuru enterprise activation evidence `
  --config datamuru.yml `
  --out .\.datamuru\activation\activation-evidence.json `
  --output json
```

The evidence report includes the activation readiness report, hosted control
plane contract, artifact checklist, and audit metadata that says the command is
offline, does not mutate provider resources, does not mutate state, and omits
secret values. If activation is blocked, the command does not write an evidence
file unless `--allow-blocked` is supplied for support triage.

## Export a full handoff package

For Cline, onboarding, or support workflows that need every redacted activation
artifact in one directory, write a package:

```powershell
datamuru enterprise activation package `
  --config datamuru.yml `
  --out .\.datamuru\activation\handoff-package `
  --output json
```

The package writes:

- `enterprise-activation.json`;
- `purchase-request.json`;
- `activation-evidence.json`;
- `control-plane-contract.json`;
- `control-plane-architecture.json`;
- `tenant-entitlement-record.json`;
- `manifest.json`.

The manifest lists artifact schema versions, ready or blocked status, and
redaction guarantees. It does not include license key values or provider token
values. If activation is blocked, the command does not write the package unless
`--allow-blocked` is supplied for support triage.

## Build a control plane contract

After activation readiness passes, build a hosted control plane contract:

```powershell
datamuru enterprise control-plane contract `
  --config datamuru.yml `
  --out .\.datamuru\activation\control-plane-contract.json `
  --output json
```

The contract is a redacted, offline handoff artifact for a future Enterprise
control plane or support workflow. It includes:

- activation readiness and redacted onboarding metadata;
- local or remote state backend posture;
- enabled feature flags;
- project paths and provider config references;
- hosted follow-up actions for entitlement, tenant binding, secret handling,
  shared state, and evidence capture.

The contract can be ready even when it contains warnings. For example, local
state is valid for OSS workflows but still warns that hosted multi-user
execution needs a shared state extension. Remote state contracts are recognized
as hosted boundaries; OSS still does not read or write remote state directly.

## Export a tenant entitlement record

Create an immutable record for reviewed onboarding or support handoff:

```powershell
datamuru enterprise control-plane tenant-record `
  --config datamuru.yml `
  --out .\.datamuru\activation\tenant-entitlement-record.json `
  --output json
```

The record binds the project, organization, tenant, deployment region, control
plane URL, support plan, purchase reference, and enabled Enterprise features.
Its `record_id` is deterministic for those stable redacted fields. Generation
time, activation checks, readiness status, and license-key availability do not
change the identifier.

The artifact records the license environment-variable name and whether the
variable is available, but never includes the secret value or an absolute local
project path. This OSS command does not create a hosted registry entry or
provision a tenant. Those capabilities remain roadmap work.

## What the check validates

The preflight fails when:

- the project is not using `project.edition: enterprise`;
- `features.hosted_control_plane` is not enabled;
- `enterprise.activation` is missing;
- required activation fields are blank;
- `contact_email` is not shaped like an email address;
- the configured license key environment variable is not set.

Passing the preflight does not provision a tenant. It confirms that the OSS
configuration is ready for the Enterprise control plane or support team to
complete activation.
