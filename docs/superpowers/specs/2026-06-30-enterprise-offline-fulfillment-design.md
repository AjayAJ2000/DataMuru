# Enterprise offline fulfillment design

## Status

Approved for the final `0.5.0a0` milestone implementation slice.

## Objective

Complete the open-source boundary of the Enterprise purchase and license
activation flow with an auditable, deterministic, and redacted offline
fulfillment workflow. The workflow records a human commercial decision and
produces artifacts that a future private hosted control plane can ingest.

This feature does not process payment, issue a cryptographically signed license,
provision a tenant, contact a license server, or activate a hosted service.

## User workflow

An operator starts from a DataMuru Enterprise purchase-request JSON artifact and
runs `datamuru enterprise activation fulfill`. The command requires:

- an explicit `approve` or `reject` decision;
- an operator identifier;
- a decision reference;
- an output directory;
- optional decision notes.

The command validates the complete input before writing anything. An approved
request produces a fulfillment decision record and an activation receipt. A
rejected request produces only the decision record because no entitlement was
issued.

## Components

### Fulfillment input validation

The loader accepts only `datamuru.enterprise_purchase_request.v1`. It verifies
the required request sections, request readiness, tenant identity, requested
entitlements, license redaction fields, and offline/non-provisioning flags.

Approval is blocked when the request is marked blocked, contains secret-bearing
metadata, claims that it provisions a tenant or calls a license server, or is
structurally incomplete. Rejection remains available for a structurally valid
request regardless of readiness so an operator can record why fulfillment did
not proceed.

### Fulfillment decision record

The decision record uses schema
`datamuru.enterprise_fulfillment_decision.v1`. It contains:

- the decision and decision timestamp;
- operator identifier and decision reference;
- optional notes;
- a SHA-256 fingerprint of the canonical redacted purchase request;
- stable tenant and commercial identifiers from the request;
- approved or rejected requested entitlements;
- explicit security and non-provisioning declarations.

The record never includes a token, license secret, provider credential, or
unredacted environment value.

### Activation receipt

Approved requests also produce
`datamuru.enterprise_activation_receipt.v1`. The receipt binds the approved
entitlements to the source request fingerprint and decision-record fingerprint.
It has a deterministic receipt identifier derived from stable redacted fields.
Generation timestamps may differ between runs, but identifiers and source
fingerprints remain stable for identical inputs and decisions.

The receipt states that it is an offline handoff artifact, not a signed license,
proof of payment, or proof of tenant provisioning.

### CLI and Python API

The CLI command is:

```text
datamuru enterprise activation fulfill \
  --request <purchase-request.json> \
  --decision approve|reject \
  --operator <operator-id> \
  --decision-reference <reference> \
  --out <directory> \
  [--notes <text>] \
  [--output text|json]
```

The Python API exposes pure builders, a validated request loader, and a writer
that creates the output directory atomically enough to avoid partial success:
all artifacts are built and serialized before any destination file is written.
Existing files are not overwritten unless the generated content is identical.

## Data and error flow

1. Load JSON and validate its schema and shape.
2. Canonicalize the redacted request and calculate its SHA-256 fingerprint.
3. Validate decision-specific rules.
4. Build and fully serialize the decision record.
5. For approval, build and fully serialize the activation receipt.
6. Reject conflicting existing output before writing.
7. Write the complete artifact set and return paths plus fingerprints.

Malformed JSON, unsupported schema versions, missing fields, unsafe redaction
posture, blocked approvals, invalid decisions, blank operator evidence, and
conflicting output files produce structured DataMuru errors. Error messages do
not echo arbitrary request content or secret-like values.

## Handoff-package integration

The existing activation handoff package remains a pre-fulfillment package. It
continues to contain the purchase request and tenant entitlement proposal. The
new fulfillment output is a separate post-decision directory so generated
commercial evidence cannot be mistaken for project-authored onboarding input.

Documentation links the two stages but does not silently add an approval or
receipt to the pre-fulfillment package.

## Security boundaries

- No network calls.
- No provider or state mutation.
- No payment processing.
- No tenant provisioning.
- No license-server interaction.
- No token or license-secret generation.
- No cryptographic-signature claim.
- No overwrite of conflicting evidence.
- No raw request echo in errors.
- Explicit fingerprints bind outputs to their source artifacts.

Cryptographic signing, payment verification, private package access, hosted
tenant creation, and license validation remain responsibilities of a future
private Enterprise control plane.

## Testing

Tests cover:

- approved and rejected CLI workflows;
- required operator and decision-reference evidence;
- Python builders and writers;
- malformed and unsupported request files;
- blocked-request approval refusal;
- rejection of secret-bearing or provisioning-claim inputs;
- deterministic request, decision, and receipt fingerprints;
- generation-time independence of stable identifiers;
- conflicting-output protection and identical reruns;
- absence of configured license and provider secrets in stdout and files;
- text and JSON output contracts;
- documentation navigation and runbook coverage;
- the complete unit and end-to-end suite, Ruff, strict MkDocs, package build,
  and Twine checks.

The milestone runbook will include feature-by-feature PowerShell commands,
expected outputs, tamper tests, redaction checks, rerun behavior, and a bug
report template suitable for Cline-based enterprise testing.

## Delivery

The implementation updates the changelog, Enterprise activation guide, CLI and
Python references, canonical capability page, milestone `0.5.0a0` runbook,
roadmap, and GitHub Project evidence. The project item can move to Done only
after local verification, push, and successful GitHub pipelines.
