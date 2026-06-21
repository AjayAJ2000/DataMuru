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
