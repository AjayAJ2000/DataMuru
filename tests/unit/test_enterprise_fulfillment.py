from __future__ import annotations

from copy import deepcopy
import json
from typing import Any

import pytest

from datamuru.enterprise.fulfillment import (
    canonical_json,
    load_purchase_request,
    purchase_request_fingerprint,
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
