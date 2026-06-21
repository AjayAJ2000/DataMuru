# Milestone 0.5 test runbook

Use this runbook to test the 0.5.0a0 milestone features end to end. Run each
feature independently and capture the command, output, generated files, and any
redacted configuration snippets when reporting bugs.

## Scope

This runbook covers:

- the `enterprise.activation` root configuration contract;
- Enterprise activation readiness checks for hosted control plane onboarding;
- text and JSON output from `datamuru enterprise activation check`;
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

## 7. Python API activation report

Run this from the repository root or an environment where DataMuru is installed:

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

## 8. Documentation and schema coverage

Confirm the milestone docs are discoverable:

```powershell
python -m pytest tests\unit\test_documentation.py -q
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

## 9. Local quality gate

Run this before reporting the milestone as tested:

```powershell
python -m ruff check datamuru tests
python -m pytest -q --basetemp .datamuru\pytest-tmp -p no:cacheprovider
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
- whether the failure is reproducible on a second run.

Do not include provider tokens, license keys, private keys, customer data, or
raw state files.
