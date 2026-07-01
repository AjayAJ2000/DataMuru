from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
import json
from types import MappingProxyType
from typing import Any

import pytest
from click.testing import CliRunner

from datamuru.api import DataMuru
from datamuru.cli.main import cli
from datamuru.enterprise.activation import (
    ActivationReport,
    LICENSE_SECRET_HANDLING,
    build_activation_purchase_request,
)
from datamuru.enterprise.fulfillment import (
    build_fulfillment,
    canonical_json,
    load_purchase_request,
    purchase_request_fingerprint,
    validate_purchase_request,
    write_fulfillment,
)
from datamuru.errors import EnterpriseFulfillmentError


@pytest.fixture
def ready_purchase_request() -> dict[str, Any]:
    return {
        "schema_version": "datamuru.enterprise_purchase_request.v1",
        "generated_at": "2026-06-30T09:00:00Z",
        "status": "ready",
        "report": {"ready": True},
        "commercial": {
            "organization": "Acme Data",
            "contact_email": "licensing@acme.example",
            "purchase_reference": "PO-12345",
            "support_plan": "enterprise",
            "requested_entitlements": ["hosted_control_plane"],
        },
        "fulfillment": {
            "tenant_id": "acme-prod",
            "deployment_region": "us-east-1",
            "control_plane_url": "https://control.datamuru.example",
            "offline": True,
            "provisions_tenant": False,
            "calls_license_server": False,
        },
        "license": {
            "license_key_env": "DATAMURU_LICENSE_KEY",
            "license_key_present": True,
            "secret_values_included": False,
            "secret_handling": LICENSE_SECRET_HANDLING,
        },
    }


def test_loads_ready_purchase_request_and_builds_fingerprint(
    tmp_path, ready_purchase_request
):
    path = tmp_path / "purchase-request.json"
    path.write_text(json.dumps(ready_purchase_request), encoding="utf-8")

    request = load_purchase_request(path)

    assert request == ready_purchase_request
    assert request["schema_version"] == "datamuru.enterprise_purchase_request.v1"
    assert purchase_request_fingerprint(request).startswith("sha256:")


def test_canonical_json_is_sorted_compact_and_ascii():
    assert canonical_json({"z": "caf\u00e9", "a": {"b": 1}}) == (
        '{"a":{"b":1},"z":"caf\\u00e9"}'
    )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_canonical_json_rejects_nonfinite_numbers_with_safe_error(value):
    with pytest.raises(EnterpriseFulfillmentError) as exc_info:
        canonical_json({"untrusted": value})

    assert exc_info.value.code == "DMR-ENT-1001"
    assert str(exc_info.value) == "Canonical JSON contains unsupported values."


def _freeze_mappings(value):
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze_mappings(item) for key, item in value.items()})
    if isinstance(value, list):
        return [_freeze_mappings(item) for item in value]
    return value


def test_validation_and_fingerprint_accept_mapping_inputs(ready_purchase_request):
    request = _freeze_mappings(ready_purchase_request)

    validate_purchase_request(request, for_approval=True)

    assert canonical_json(request) == canonical_json(ready_purchase_request)
    assert purchase_request_fingerprint(request) == purchase_request_fingerprint(
        ready_purchase_request
    )


@pytest.mark.parametrize(
    "secret_key",
    [
        "license_key",
        "raw_token",
        "password",
        "credential",
        "access_key",
        "api_key",
        "private_key",
        "client_secret",
        "rawToken",
        "refreshToken",
        "secret_value",
        "token_value",
        "aws_secret_access_key",
        "AwsSecretAccessKey",
        "token-value",
        "secret value",
        "Authorization",
        "auth_header",
        "bearer",
        "session_cookie",
    ],
)
def test_rejects_recursive_secret_bearing_keys_without_disclosing_values(
    ready_purchase_request, secret_key
):
    request = deepcopy(ready_purchase_request)
    if secret_key == "license_key":
        request["license"][secret_key] = "secret-value"
    else:
        request["report"]["nested"] = {secret_key: "secret-value"}

    with pytest.raises(EnterpriseFulfillmentError) as exc_info:
        validate_purchase_request(request, for_approval=False)

    assert exc_info.value.code == "DMR-ENT-1001"
    assert "secret-value" not in str(exc_info.value)


@pytest.mark.parametrize(
    ("metadata_key", "malicious_value"),
    [
        ("license_key_env", "DATAMURU_LICENSE_KEY;REMOVE_ALL"),
        ("license_key_env", "DATAMURU LICENSE KEY"),
        ("license_key_env", "DATAMURU/LICENSE_KEY"),
        ("license_key_env", "secret-value"),
        ("license_key_env", "sk_live_ABC123"),
        ("license_key_env", "FOO"),
        ("license_key_present", "true"),
        ("secret_values_included", 0),
        ("secret_handling", f"{LICENSE_SECRET_HANDLING} secret-value"),
    ],
)
def test_rejects_invalid_safe_secret_metadata_values(
    ready_purchase_request, metadata_key, malicious_value
):
    request = deepcopy(ready_purchase_request)
    request["report"]["nested"] = {metadata_key: malicious_value}

    with pytest.raises(EnterpriseFulfillmentError) as exc_info:
        validate_purchase_request(request, for_approval=False)

    assert exc_info.value.code == "DMR-ENT-1001"
    assert "secret-value" not in str(exc_info.value)


@pytest.mark.parametrize(
    "license_key_env",
    ["DATAMURU_LICENSE_KEY", "datamuru_License_key"],
)
def test_accepts_purchase_request_generated_by_activation_producer(license_key_env):
    report = ActivationReport(
        project="analytics-platform",
        edition="enterprise",
        provider="databricks",
        default_environment="prod",
        ready=True,
        payload={
            "activation": {
                "organization": "Acme Data",
                "contact_email": "platform@acme.test",
                "tenant_id": "acme-prod",
                "deployment_region": "us-east-1",
                "control_plane_url": "https://control.datamuru.example",
                "license_key_env": license_key_env,
                "license_key_present": True,
            },
            "features": {"hosted_control_plane": True},
        },
        checks=[],
    )
    request = build_activation_purchase_request(report).to_dict()

    validate_purchase_request(request, for_approval=True)


@pytest.mark.parametrize(
    ("metadata_key", "metadata_value"),
    [("token_count", 0), ("credential_source", "environment")],
)
def test_accepts_non_secret_metadata_with_security_words(
    ready_purchase_request, metadata_key, metadata_value
):
    request = deepcopy(ready_purchase_request)
    request["report"]["nested"] = {metadata_key: metadata_value}

    validate_purchase_request(request, for_approval=True)


@pytest.mark.parametrize("field", ["purchase_reference", "support_plan"])
@pytest.mark.parametrize(
    "optional_value",
    [pytest.param(None, id="null"), pytest.param("missing", id="missing")],
)
def test_accepts_missing_or_null_optional_commercial_fields(
    ready_purchase_request, field, optional_value
):
    request = deepcopy(ready_purchase_request)
    if optional_value == "missing":
        del request["commercial"][field]
    else:
        request["commercial"][field] = optional_value

    validate_purchase_request(request, for_approval=False)


@pytest.mark.parametrize(
    ("status", "report"),
    [
        ("blocked", {"ready": True}),
        ("ready", {}),
        ("ready", {"ready": False}),
        ("ready", {"ready": 1}),
        ("ready", {"details": "present"}),
    ],
)
def test_approval_requires_consistent_ready_status_and_report(
    ready_purchase_request, status, report
):
    request = deepcopy(ready_purchase_request)
    request["status"] = status
    request["report"] = report

    with pytest.raises(EnterpriseFulfillmentError) as exc_info:
        validate_purchase_request(request, for_approval=True)

    assert exc_info.value.code == "DMR-ENT-1001"


@pytest.mark.parametrize(
    "field",
    [
        "organization",
        "contact_email",
        "requested_entitlements",
    ],
)
def test_validation_requires_commercial_identifiers(ready_purchase_request, field):
    request = deepcopy(ready_purchase_request)
    request["commercial"][field] = [] if field == "requested_entitlements" else "   "

    with pytest.raises(EnterpriseFulfillmentError) as exc_info:
        validate_purchase_request(request, for_approval=False)

    assert exc_info.value.code == "DMR-ENT-1001"


def _invalid_request(
    ready_request: dict[str, Any], case: str
) -> dict[str, Any] | str:
    request = deepcopy(ready_request)
    request["untrusted_note"] = "secret-value"

    if case == "malformed_json":
        return '{"untrusted_note":"secret-value"'
    if case == "unsupported_schema":
        request["schema_version"] = "secret-value"
    elif case == "missing_commercial":
        del request["commercial"]
    elif case == "missing_tenant_identity":
        del request["fulfillment"]["tenant_id"]
    elif case == "secret_values_included":
        request["license"]["secret_values_included"] = True
    elif case == "provisions_tenant":
        request["fulfillment"]["provisions_tenant"] = True
    elif case == "calls_license_server":
        request["fulfillment"]["calls_license_server"] = True
    else:  # pragma: no cover - protects the test helper from invalid cases
        raise AssertionError(f"Unknown invalid request case: {case}")
    return request


@pytest.mark.parametrize(
    "case",
    [
        "malformed_json",
        "unsupported_schema",
        "missing_commercial",
        "missing_tenant_identity",
        "secret_values_included",
        "provisions_tenant",
        "calls_license_server",
    ],
)
def test_rejects_invalid_purchase_requests_without_disclosing_values(
    tmp_path, ready_purchase_request, case
):
    payload = _invalid_request(ready_purchase_request, case)
    path = tmp_path / f"{case}.json"
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(EnterpriseFulfillmentError) as exc_info:
        load_purchase_request(path)

    assert exc_info.value.code == "DMR-ENT-1001"
    assert "secret-value" not in str(exc_info.value)


def test_builds_approved_decision_and_activation_receipt(ready_purchase_request):
    decision, receipt = build_fulfillment(
        ready_purchase_request,
        decision="approve",
        operator="licensing@datamuru.com",
        decision_reference="CRM-1234",
        notes="Commercial review complete.",
        generated_at=datetime(2026, 7, 1, 8, 30, tzinfo=UTC),
    )

    assert decision.schema_version == "datamuru.enterprise_fulfillment_decision.v1"
    assert decision.decision == "approve"
    assert decision.decision_id.startswith("fdr_")
    assert decision.operator == "licensing@datamuru.com"
    assert decision.entitlements["approved"] == ["hosted_control_plane"]
    assert decision.entitlements["rejected"] == []
    assert decision.security == {
        "offline": True,
        "payment_processed": False,
        "cryptographically_signed": False,
        "calls_license_server": False,
        "provisions_tenant": False,
        "secret_values_included": False,
    }

    assert receipt is not None
    assert receipt.schema_version == "datamuru.enterprise_activation_receipt.v1"
    assert receipt.receipt_id.startswith("far_")
    assert receipt.decision_id == decision.decision_id
    assert receipt.source_request_fingerprint == decision.source_request_fingerprint
    assert receipt.entitlement["enabled_features"] == ["hosted_control_plane"]
    assert receipt.security["cryptographically_signed"] is False
    assert receipt.security["provisions_tenant"] is False


def test_builds_rejection_without_activation_receipt(ready_purchase_request):
    request = deepcopy(ready_purchase_request)
    request["status"] = "blocked"
    request["report"] = {"ready": False}

    decision, receipt = build_fulfillment(
        request,
        decision="reject",
        operator="licensing@datamuru.com",
        decision_reference="CRM-1235",
        generated_at=datetime(2026, 7, 1, 8, 30, tzinfo=UTC),
    )

    assert decision.decision == "reject"
    assert decision.entitlements["approved"] == []
    assert decision.entitlements["rejected"] == ["hosted_control_plane"]
    assert receipt is None


def test_fulfillment_ids_are_stable_across_generation_times(ready_purchase_request):
    first_decision, first_receipt = build_fulfillment(
        ready_purchase_request,
        decision="approve",
        operator="licensing@datamuru.com",
        decision_reference="CRM-1234",
        generated_at=datetime(2026, 7, 1, 8, 30, tzinfo=UTC),
    )
    second_decision, second_receipt = build_fulfillment(
        ready_purchase_request,
        decision="approve",
        operator="licensing@datamuru.com",
        decision_reference="CRM-1234",
        generated_at=datetime(2026, 7, 2, 9, 45, tzinfo=UTC),
    )

    assert first_receipt is not None and second_receipt is not None
    assert first_decision.generated_at != second_decision.generated_at
    assert first_decision.decision_id == second_decision.decision_id
    assert first_decision.decision_fingerprint == second_decision.decision_fingerprint
    assert first_receipt.receipt_id == second_receipt.receipt_id
    assert first_receipt.decision_fingerprint == second_receipt.decision_fingerprint


@pytest.mark.parametrize(
    ("operator", "decision_reference"),
    [("", "CRM-1234"), ("   ", "CRM-1234"), ("licensing@datamuru.com", "")],
)
def test_fulfillment_requires_operator_evidence(
    ready_purchase_request, operator, decision_reference
):
    with pytest.raises(EnterpriseFulfillmentError):
        build_fulfillment(
            ready_purchase_request,
            decision="approve",
            operator=operator,
            decision_reference=decision_reference,
        )


def test_fulfillment_blocks_approval_of_blocked_request(ready_purchase_request):
    request = deepcopy(ready_purchase_request)
    request["status"] = "blocked"
    request["report"] = {"ready": False}

    with pytest.raises(EnterpriseFulfillmentError) as exc_info:
        build_fulfillment(
            request,
            decision="approve",
            operator="licensing@datamuru.com",
            decision_reference="CRM-1234",
        )

    assert "blocked" in str(exc_info.value).casefold()


def _write_request(tmp_path, request):
    request_path = tmp_path / "purchase-request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    return request_path


def test_writer_creates_approved_decision_and_receipt(tmp_path, ready_purchase_request):
    request_path = _write_request(tmp_path, ready_purchase_request)
    output_dir = tmp_path / "fulfillment"

    result = write_fulfillment(
        request_path,
        output_dir,
        decision="approve",
        operator="licensing@datamuru.com",
        decision_reference="CRM-1234",
    )

    assert result.decision_path == str((output_dir / "fulfillment-decision.json").resolve())
    assert result.receipt_path == str((output_dir / "activation-receipt.json").resolve())
    assert (output_dir / "fulfillment-decision.json").exists()
    assert (output_dir / "activation-receipt.json").exists()
    assert result.receipt is not None


def test_writer_creates_rejection_without_receipt(tmp_path, ready_purchase_request):
    request_path = _write_request(tmp_path, ready_purchase_request)
    output_dir = tmp_path / "rejection"

    result = write_fulfillment(
        request_path,
        output_dir,
        decision="reject",
        operator="licensing@datamuru.com",
        decision_reference="CRM-1235",
    )

    assert result.receipt is None
    assert result.receipt_path is None
    assert (output_dir / "fulfillment-decision.json").exists()
    assert not (output_dir / "activation-receipt.json").exists()


def test_writer_allows_identical_rerun(tmp_path, ready_purchase_request):
    request_path = _write_request(tmp_path, ready_purchase_request)
    output_dir = tmp_path / "fulfillment"
    generated_at = datetime(2026, 7, 1, 8, 30, tzinfo=UTC)
    arguments = {
        "decision": "approve",
        "operator": "licensing@datamuru.com",
        "decision_reference": "CRM-1234",
        "generated_at": generated_at,
    }

    first = write_fulfillment(request_path, output_dir, **arguments)
    second = write_fulfillment(request_path, output_dir, **arguments)

    assert second.decision_id == first.decision_id
    assert second.receipt is not None and first.receipt is not None
    assert second.receipt.receipt_id == first.receipt.receipt_id


def test_writer_blocks_conflicting_output_before_mutation(tmp_path, ready_purchase_request):
    request_path = _write_request(tmp_path, ready_purchase_request)
    output_dir = tmp_path / "fulfillment"
    output_dir.mkdir()
    decision_path = output_dir / "fulfillment-decision.json"
    receipt_path = output_dir / "activation-receipt.json"
    decision_path.write_text('{"existing":"decision"}\n', encoding="utf-8")
    receipt_path.write_text('{"existing":"receipt"}\n', encoding="utf-8")

    with pytest.raises(EnterpriseFulfillmentError):
        write_fulfillment(
            request_path,
            output_dir,
            decision="approve",
            operator="licensing@datamuru.com",
            decision_reference="CRM-1234",
        )

    assert decision_path.read_text(encoding="utf-8") == '{"existing":"decision"}\n'
    assert receipt_path.read_text(encoding="utf-8") == '{"existing":"receipt"}\n'


def test_writer_blocks_rejection_beside_stale_receipt(tmp_path, ready_purchase_request):
    request_path = _write_request(tmp_path, ready_purchase_request)
    output_dir = tmp_path / "fulfillment"
    output_dir.mkdir()
    stale_receipt = output_dir / "activation-receipt.json"
    stale_receipt.write_text('{"stale":true}\n', encoding="utf-8")

    with pytest.raises(EnterpriseFulfillmentError):
        write_fulfillment(
            request_path,
            output_dir,
            decision="reject",
            operator="licensing@datamuru.com",
            decision_reference="CRM-1235",
        )

    assert stale_receipt.read_text(encoding="utf-8") == '{"stale":true}\n'
    assert not (output_dir / "fulfillment-decision.json").exists()


def test_python_api_fulfills_without_loading_project_config(tmp_path, ready_purchase_request):
    request_path = _write_request(tmp_path, ready_purchase_request)

    result = DataMuru.fulfill_enterprise_activation(
        request_path,
        tmp_path / "api-fulfillment",
        decision="approve",
        operator="licensing@datamuru.com",
        decision_reference="CRM-1234",
    )

    assert result.decision.decision == "approve"
    assert result.receipt is not None


def test_fulfill_cli_approves_request_with_json_output(tmp_path, ready_purchase_request):
    request_path = _write_request(tmp_path, ready_purchase_request)
    output_dir = tmp_path / "cli-approval"

    result = CliRunner().invoke(
        cli,
        [
            "enterprise",
            "activation",
            "fulfill",
            "--request",
            str(request_path),
            "--decision",
            "approve",
            "--operator",
            "licensing@datamuru.com",
            "--decision-reference",
            "CRM-1234",
            "--out",
            str(output_dir),
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["decision"]["decision"] == "approve"
    assert payload["decision"]["decision_id"].startswith("fdr_")
    assert payload["receipt"]["receipt_id"].startswith("far_")
    assert payload["decision_path"].endswith("fulfillment-decision.json")
    assert payload["receipt_path"].endswith("activation-receipt.json")


def test_fulfill_cli_rejects_request_without_receipt(tmp_path, ready_purchase_request):
    request_path = _write_request(tmp_path, ready_purchase_request)
    output_dir = tmp_path / "cli-rejection"

    result = CliRunner().invoke(
        cli,
        [
            "--no-banner",
            "enterprise",
            "activation",
            "fulfill",
            "--request",
            str(request_path),
            "--decision",
            "reject",
            "--operator",
            "licensing@datamuru.com",
            "--decision-reference",
            "CRM-1235",
            "--out",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert "rejected" in result.output.casefold()
    assert (output_dir / "fulfillment-decision.json").exists()
    assert not (output_dir / "activation-receipt.json").exists()


def test_fulfill_cli_requires_operator_evidence(tmp_path, ready_purchase_request):
    request_path = _write_request(tmp_path, ready_purchase_request)

    result = CliRunner().invoke(
        cli,
        [
            "enterprise",
            "activation",
            "fulfill",
            "--request",
            str(request_path),
            "--decision",
            "approve",
            "--out",
            str(tmp_path / "missing-evidence"),
        ],
    )

    assert result.exit_code != 0
    assert "--operator" in result.output


def test_fulfill_cli_blocks_unsafe_request_without_echoing_secret(
    tmp_path, ready_purchase_request
):
    request = deepcopy(ready_purchase_request)
    request["report"]["Authorization"] = "secret-value"
    request_path = _write_request(tmp_path, request)

    result = CliRunner().invoke(
        cli,
        [
            "--no-banner",
            "enterprise",
            "activation",
            "fulfill",
            "--request",
            str(request_path),
            "--decision",
            "approve",
            "--operator",
            "licensing@datamuru.com",
            "--decision-reference",
            "CRM-1234",
            "--out",
            str(tmp_path / "unsafe"),
        ],
    )

    assert result.exit_code == 1
    assert "credential-bearing" in result.output
    assert "secret-value" not in result.output
