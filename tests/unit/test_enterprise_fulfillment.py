from __future__ import annotations

from copy import deepcopy
import json
from types import MappingProxyType
from typing import Any

import pytest

from datamuru.enterprise.activation import (
    ActivationReport,
    build_activation_purchase_request,
)
from datamuru.enterprise.fulfillment import (
    canonical_json,
    load_purchase_request,
    purchase_request_fingerprint,
    validate_purchase_request,
)
from datamuru.errors import EnterpriseFulfillmentError


SECRET_HANDLING = (
    "The license key value is intentionally omitted. The receiving workflow must "
    "resolve the named environment variable or request the secret through an approved "
    "secret manager."
)


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
            "secret_handling": SECRET_HANDLING,
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
        ("license_key_present", "true"),
        ("secret_values_included", 0),
        ("secret_handling", f"{SECRET_HANDLING} secret-value"),
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
