# Milestone 0.5 test runbook

Use this runbook to test the 0.5.0a0 milestone features end to end. Run each
feature independently and capture the command, output, generated files, and any
redacted configuration snippets when reporting bugs.

## Scope

This runbook covers:

- the `enterprise.activation` root configuration contract;
- Enterprise activation readiness checks for hosted control plane onboarding;
- text and JSON output from `datamuru enterprise activation check`;
- redacted handoff bundle export from `datamuru enterprise activation export`;
- redacted purchase and license activation request export from
  `datamuru enterprise activation purchase-request`;
- redacted audit evidence export from `datamuru enterprise activation evidence`;
- hosted control plane reference architecture export from `datamuru enterprise control-plane architecture`;
- redacted hosted handoff contracts from `datamuru enterprise control-plane contract`;
- local and remote backend readiness output from `datamuru state inspect`;
- license key environment-variable detection without secret disclosure;
- Python API activation report generation;
- documentation and schema coverage for the activation contract.

The OSS CLI does not provision an Enterprise tenant or call a license server.
This milestone verifies the local readiness contract that a hosted Enterprise
control plane or support workflow can consume later.

## Before you start

Use a sandbox copy of a DataMuru project. Do not run these checks against a
production configuration unless secrets are stored outside YAML and outputs are
reviewed before sharing.

```powershell
python -m pip install -e ".[dev,docs]"
python -m datamuru.cli.main --no-banner validate --config datamuru.yml --strict
python -m datamuru.cli.main --no-banner enterprise activation check --config datamuru.yml
```

For an open-source project, the final command should fail. That failure is the
expected baseline because activation requires Enterprise edition settings.

Capture:

- DataMuru version or commit SHA;
- Python version;
- operating system;
- redacted `datamuru.yml`;
- exact command and full output;
- whether the command was run from an installed package or editable checkout.

Do not paste license keys, provider tokens, private keys, customer data, or raw
state files.

## 1. Open-source blocking baseline

Run against an unchanged OSS project:

```powershell
python -m datamuru.cli.main --no-banner enterprise activation check `
  --config datamuru.yml
```

Expected result:

- command exits nonzero;
- output says Enterprise activation is `blocked`;
- output includes `project.edition` guidance;
- output includes `features.hosted_control_plane` guidance;
- output includes `enterprise.activation` guidance.

Bug evidence to capture:

- command output;
- redacted `project.edition` and `features.hosted_control_plane` values.

## 2. Enterprise activation config shape

In a sandbox project, configure Enterprise activation intent:

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

Validate the project:

```powershell
python -m datamuru.cli.main --no-banner validate --config datamuru.yml --strict
```

Expected result:

- validation accepts the `enterprise.activation` block;
- no schema or Pydantic error reports `enterprise` as an unknown root key;
- no license key value is stored in YAML.

Bug evidence to capture:

- validation output;
- redacted `enterprise.activation` block.

## 3. Missing license environment variable

Run with the activation block present, but without the configured license
environment variable:

```powershell
Remove-Item Env:DATAMURU_LICENSE_KEY -ErrorAction SilentlyContinue

python -m datamuru.cli.main --no-banner enterprise activation check `
  --config datamuru.yml
```

Expected result:

- command exits nonzero;
- output says Enterprise activation is `blocked`;
- output names `enterprise.activation.license_key_env`;
- output says `DATAMURU_LICENSE_KEY` is not set;
- output does not ask the user to put the license key in YAML.

Bug evidence to capture:

- command output;
- shell environment variable name only, not the secret value.

## 4. Successful text preflight

Set a non-production test license value in the environment:

```powershell
$env:DATAMURU_LICENSE_KEY="test-license-value"

python -m datamuru.cli.main --no-banner enterprise activation check `
  --config datamuru.yml
```

Expected result:

- command exits successfully;
- output says Enterprise activation is `ready`;
- output names the project and provider;
- output says the activation payload is ready for onboarding;
- output does not print `test-license-value`.

Bug evidence to capture:

- command output;
- confirmation that the literal license value is absent from output.

## 5. Successful JSON preflight

Run the JSON form for automation:

```powershell
python -m datamuru.cli.main --no-banner enterprise activation check `
  --config datamuru.yml `
  --output json
```

Expected result:

- stdout is valid JSON;
- top-level `ready` is `true`;
- `payload.schema_version` is `datamuru.enterprise_activation.v1`;
- `payload.activation.license_key_env` is `DATAMURU_LICENSE_KEY`;
- `payload.activation.license_key_present` is `true`;
- the literal license value is absent from stdout;
- `checks` is an empty list.

Optional parser check:

```powershell
$json = python -m datamuru.cli.main --no-banner enterprise activation check `
  --config datamuru.yml `
  --output json | ConvertFrom-Json

$json.ready
$json.payload.activation.license_key_present
$json.checks.Count
```

Expected parser values:

- `True`;
- `True`;
- `0`.

## 6. Invalid contact email

Change only `contact_email` to an invalid value:

```yaml
enterprise:
  activation:
    contact_email: platform-contact
```

Run:

```powershell
python -m datamuru.cli.main --no-banner enterprise activation check `
  --config datamuru.yml
```

Expected result:

- command exits nonzero;
- output names `enterprise.activation.contact_email`;
- output explains that the value must be an email address.

Restore a valid email before continuing.

## 7. Activation handoff bundle export

Run the export command with a ready activation config:

```powershell
python -m datamuru.cli.main --no-banner enterprise activation export `
  --config datamuru.yml `
  --out .\.datamuru\activation\enterprise-activation.json `
  --output json
```

Expected result:

- command exits successfully;
- `.datamuru/activation/enterprise-activation.json` exists;
- JSON command output includes `ready: true`;
- bundle `schema_version` is `datamuru.enterprise_activation_bundle.v1`;
- bundle `status` is `ready`;
- bundle embeds the redacted activation report;
- the literal license value is absent from the bundle.

Blocked export check:

```powershell
Remove-Item Env:DATAMURU_LICENSE_KEY -ErrorAction SilentlyContinue

python -m datamuru.cli.main --no-banner enterprise activation export `
  --config datamuru.yml `
  --out .\.datamuru\activation\blocked.json
```

Expected result:

- command exits nonzero;
- `blocked.json` is not written;
- output explains which checks failed.

Use this diagnostic path only when support requests a blocked bundle:

```powershell
python -m datamuru.cli.main --no-banner enterprise activation export `
  --config datamuru.yml `
  --out .\.datamuru\activation\blocked.json `
  --allow-blocked
```

Expected result:

- command exits successfully;
- bundle `status` is `blocked`;
- failed checks are present;
- no secret value is present.

## 8. Purchase and license activation request

Run the purchase-request command with a ready activation config:

```powershell
$env:DATAMURU_LICENSE_KEY="test-license-value"

python -m datamuru.cli.main --no-banner enterprise activation purchase-request `
  --config datamuru.yml `
  --out .\.datamuru\activation\purchase-request.json `
  --output json
```

Expected result:

- command exits successfully;
- `.datamuru/activation/purchase-request.json` exists;
- JSON command output includes `ready: true`;
- request `schema_version` is `datamuru.enterprise_purchase_request.v1`;
- request `status` is `ready`;
- request includes `commercial.purchase_reference` and `commercial.support_plan`;
- request includes requested entitlements such as `hosted_control_plane`;
- request `fulfillment.offline` is `true`;
- request `fulfillment.provisions_tenant` is `false`;
- request `fulfillment.calls_license_server` is `false`;
- request `license.secret_values_included` is `false`;
- the literal license value is absent from stdout and the file.

Blocked request check:

```powershell
Remove-Item Env:DATAMURU_LICENSE_KEY -ErrorAction SilentlyContinue

python -m datamuru.cli.main --no-banner enterprise activation purchase-request `
  --config datamuru.yml `
  --out .\.datamuru\activation\blocked-purchase-request.json
```

Expected result:

- command exits nonzero;
- `blocked-purchase-request.json` is not written;
- output explains which activation checks failed.

Use this diagnostic path only when support requests a blocked purchase request:

```powershell
python -m datamuru.cli.main --no-banner enterprise activation purchase-request `
  --config datamuru.yml `
  --out .\.datamuru\activation\blocked-purchase-request.json `
  --allow-blocked `
  --output json
```

Expected result:

- command exits successfully;
- request `status` is `blocked`;
- failed activation checks are present;
- license metadata still says no secret values are included.

## 9. Activation audit evidence export

Run the evidence export command with a ready activation config:

```powershell
$env:DATAMURU_LICENSE_KEY="test-license-value"

python -m datamuru.cli.main --no-banner enterprise activation evidence `
  --config datamuru.yml `
  --out .\.datamuru\activation\activation-evidence.json `
  --output json
```

Expected result:

- command exits successfully;
- `.datamuru/activation/activation-evidence.json` exists;
- JSON command output includes `ready: true`;
- evidence `schema_version` is `datamuru.enterprise_activation_evidence.v1`;
- evidence `status` is `ready`;
- evidence embeds the redacted activation readiness report;
- evidence embeds the hosted control plane contract;
- evidence `audit.offline` is `true`;
- evidence `audit.mutates_provider` is `false`;
- evidence `audit.mutates_state` is `false`;
- evidence `audit.secret_values_included` is `false`;
- the literal license value is absent from stdout and the file.

Blocked evidence check:

```powershell
Remove-Item Env:DATAMURU_LICENSE_KEY -ErrorAction SilentlyContinue

python -m datamuru.cli.main --no-banner enterprise activation evidence `
  --config datamuru.yml `
  --out .\.datamuru\activation\blocked-evidence.json
```

Expected result:

- command exits nonzero;
- `blocked-evidence.json` is not written;
- output explains which checks failed.

Use this diagnostic path only when support requests blocked audit evidence:

```powershell
python -m datamuru.cli.main --no-banner enterprise activation evidence `
  --config datamuru.yml `
  --out .\.datamuru\activation\blocked-evidence.json `
  --allow-blocked `
  --output json
```

Expected result:

- command exits successfully;
- evidence `status` is `blocked`;
- failed activation checks are present;
- audit metadata still says no provider mutation, no state mutation, and no
  secret values included.

## 10. Python API activation report

Run this from a sandbox DataMuru project root or an environment where DataMuru
is installed:

```powershell
python -c "import os, json; from datamuru.api import DataMuru; os.environ['DATAMURU_LICENSE_KEY']='test-license-value'; report=DataMuru('datamuru.yml').enterprise_activation_report(); print(json.dumps(report.to_dict(), indent=2))"
```

Expected result:

- JSON output matches the CLI payload structure;
- `ready` is `true`;
- `checks` is empty;
- the literal license value is absent from output.

Bug evidence to capture:

- command output;
- whether the API behavior differs from CLI behavior.

Also verify the purchase request API:

```powershell
python -c "import os, json; from datamuru.api import DataMuru; os.environ['DATAMURU_LICENSE_KEY']='test-license-value'; request=DataMuru('datamuru.yml').enterprise_activation_purchase_request(); print(json.dumps(request.to_dict(), indent=2))"
```

Expected result:

- `schema_version` is `datamuru.enterprise_purchase_request.v1`;
- `status` is `ready`;
- the literal license value is absent from output.

## 11. Hosted control plane reference architecture

Run the architecture export command:

```powershell
python -m datamuru.cli.main --no-banner enterprise control-plane architecture `
  --config datamuru.yml `
  --out .\.datamuru\control-plane\architecture.json `
  --output json
```

Expected result:

- command exits successfully;
- stdout is valid JSON;
- `.datamuru/control-plane/architecture.json` exists;
- `schema_version` is `datamuru.hosted_control_plane_architecture.v1`;
- `status` is `reference-architecture`;
- `components` includes `oss_cli_and_python_api`, `hosted_control_plane_api`,
  `job_runner`, `state_extension`, and `audit_evidence_store`;
- `decisions` includes `HCP-001`, `HCP-002`, `HCP-003`, and `HCP-004`;
- `implementation_backlog` includes `HCP-B3` for the remote state extension;
- `non_goals` state that secret values must not be stored in project YAML.

Optional parser check:

```powershell
$json = python -m datamuru.cli.main --no-banner enterprise control-plane architecture `
  --config datamuru.yml `
  --output json | ConvertFrom-Json

$json.schema_version
$json.status
$json.components.Count
$json.implementation_backlog.Count
```

Expected parser values:

- `datamuru.hosted_control_plane_architecture.v1`;
- `reference-architecture`;
- at least `5`;
- at least `5`.

Bug evidence to capture:

- command output;
- generated architecture file;
- whether any generated architecture field conflicts with the current hosted
  control plane product direction.

## 12. Hosted control plane handoff contract

Run the contract command with a ready Enterprise activation config:

```powershell
$env:DATAMURU_LICENSE_KEY="test-license-value"

python -m datamuru.cli.main --no-banner enterprise control-plane contract `
  --config datamuru.yml `
  --out .\.datamuru\activation\control-plane-contract.json `
  --output json
```

Expected result:

- command exits successfully;
- stdout is valid JSON;
- `.datamuru/activation/control-plane-contract.json` exists;
- `schema_version` is `datamuru.hosted_control_plane_contract.v1`;
- top-level `ready` is `true`;
- `activation.ready` is `true`;
- `integration.tenant_id` matches `enterprise.activation.tenant_id`;
- `integration.license_key_env` is `DATAMURU_LICENSE_KEY`;
- `integration.license_key_present` is `true`;
- `state.backend` matches the configured state backend;
- the literal `test-license-value` is absent from stdout and the file.

Optional parser check:

```powershell
$json = python -m datamuru.cli.main --no-banner enterprise control-plane contract `
  --config datamuru.yml `
  --output json | ConvertFrom-Json

$json.schema_version
$json.ready
$json.integration.tenant_id
$json.integration.license_key_present
$json.state.backend
```

Expected parser values:

- `datamuru.hosted_control_plane_contract.v1`;
- `True`;
- the configured tenant id;
- `True`;
- the configured state backend.

Review warning checks:

- `control_plane.state.local_single_user` is expected for local state;
- `control_plane.state.remote_extension_required` is expected for recognized
  remote state contracts such as `s3`;
- warnings do not block a handoff contract when activation has passed.

Bug evidence to capture:

- command output;
- generated contract file with secrets redacted;
- redacted `enterprise.activation` and `state` blocks;
- confirmation that no tenant provisioning, license-server call, or cloud
  state access occurred.

## 13. State backend readiness inspection

Run the local backend inspection from a sandbox project:

```powershell
python -m datamuru.cli.main --no-banner state inspect `
  --config datamuru.yml `
  --output json
```

Expected result:

- stdout is valid JSON;
- command exits successfully;
- `backend` is `local`;
- `remote` is `false`;
- `runtime_supported` is `true`;
- `mode` is `read-write`;
- `success` is `true`;
- checks include `state.local.supported`.

Optional parser check:

```powershell
$json = python -m datamuru.cli.main --no-banner state inspect `
  --config datamuru.yml `
  --output json | ConvertFrom-Json

$json.backend
$json.runtime_supported
$json.mode
$json.success
```

Expected parser values:

- `local`;
- `True`;
- `read-write`;
- `True`.

In the sandbox copy, change only the state backend to a remote contract:

```yaml
state:
  backend: s3
  path: s3://acme-datamuru-state/prod/datamuru-state.json
```

Run:

```powershell
python -m datamuru.cli.main --no-banner state inspect `
  --config datamuru.yml `
  --output json
```

Expected result:

- command exits nonzero;
- stdout is still valid JSON;
- `backend` is `s3`;
- `remote` is `true`;
- `runtime_supported` is `false`;
- `mode` is `contract-only`;
- `success` is `false`;
- checks include `state.s3.not_implemented`;
- the command does not require AWS credentials and does not perform a cloud
  network call.

Restore `state.backend: local` before running plan, apply, adoption, or
destructive tests in the OSS runtime.

Bug evidence to capture:

- local and remote command output;
- redacted `state` block;
- whether any provider credential prompt or cloud access occurred.

## 14. Documentation and schema coverage

Confirm the milestone docs are discoverable:

```powershell
python -m pytest tests\unit\test_documentation.py -q
$env:NO_MKDOCS_2_WARNING = "1"
python -m mkdocs build --strict
```

Expected result:

- MkDocs nav includes this runbook;
- links in activation docs resolve;
- docs build strictly;
- the Material for MkDocs upstream warning, if present, is not a DataMuru docs
  failure.

Review these pages manually:

- `docs/guides/enterprise-activation.md`;
- `docs/reference/cli.md`;
- `docs/reference/root-config.md`;
- `docs/operations/milestone-0-5-test-runbook.md`.

## 15. Local quality gate

Run this before reporting the milestone as tested:

```powershell
python -m ruff check datamuru tests
python -m pytest -q --basetemp .datamuru\pytest-tmp -p no:cacheprovider
$env:NO_MKDOCS_2_WARNING = "1"
python -m mkdocs build --strict
```

Expected result:

- lint passes;
- unit and e2e tests pass;
- documentation builds strictly.

If pytest cannot create temp files under the default Windows temp directory,
use the `--basetemp .datamuru\pytest-tmp -p no:cacheprovider` form shown
above.

## Bug report template

When a test fails, capture:

- feature under test;
- exact command;
- full output;
- expected result from this runbook;
- actual result;
- redacted `datamuru.yml` snippet;
- whether `DATAMURU_LICENSE_KEY` was set;
- whether the literal secret appeared in output;
- whether any evidence file was written when the command was expected to block;
- whether the failure is reproducible on a second run.

Do not include provider tokens, license keys, private keys, customer data, or
raw state files.
