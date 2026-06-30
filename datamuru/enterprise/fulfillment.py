from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
from typing import Any

from datamuru.errors import EnterpriseFulfillmentError


PURCHASE_REQUEST_SCHEMA = "datamuru.enterprise_purchase_request.v1"
SUPPORTED_PURCHASE_REQUEST_SCHEMAS = frozenset({PURCHASE_REQUEST_SCHEMA})


def load_purchase_request(path: str | Path) -> dict[str, Any]:
    try:
        raw_request = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise EnterpriseFulfillmentError(
            "Purchase request could not be read.",
            context={"path": "request"},
        ) from exc

    try:
        request = json.loads(raw_request)
    except json.JSONDecodeError as exc:
        raise EnterpriseFulfillmentError(
            "Purchase request is not valid JSON.",
            context={"path": "request"},
        ) from exc

    if type(request) is not dict:
        _raise_validation_error("Purchase request must be a JSON object.", "request")

    validate_purchase_request(request, for_approval=False)
    return request


def validate_purchase_request(
    request: Mapping[str, Any],
    *,
    for_approval: bool,
) -> None:
    if type(request) is not dict:
        _raise_validation_error("Purchase request must be a JSON object.", "request")
    if type(for_approval) is not bool:
        _raise_validation_error("Approval validation mode must be a boolean.", "for_approval")

    schema_version = request.get("schema_version")
    if type(schema_version) is not str or schema_version not in SUPPORTED_PURCHASE_REQUEST_SCHEMAS:
        _raise_validation_error(
            "Purchase request schema is unsupported.",
            "schema_version",
        )

    status = request.get("status")
    if type(status) is not str or status not in {"ready", "blocked"}:
        _raise_validation_error("Purchase request status is invalid.", "status")
    if for_approval and status != "ready":
        _raise_validation_error("Blocked purchase requests cannot be approved.", "status")

    report = request.get("report")
    if type(report) is not dict:
        _raise_validation_error("Purchase request report is required.", "report")

    commercial = request.get("commercial")
    if type(commercial) is not dict:
        _raise_validation_error("Commercial request details are required.", "commercial")

    requested_entitlements = commercial.get("requested_entitlements")
    if (
        type(requested_entitlements) is not list
        or not requested_entitlements
        or any(type(item) is not str or not item.strip() for item in requested_entitlements)
    ):
        _raise_validation_error(
            "At least one requested entitlement is required.",
            "commercial.requested_entitlements",
        )

    fulfillment = request.get("fulfillment")
    if type(fulfillment) is not dict:
        _raise_validation_error("Fulfillment request details are required.", "fulfillment")

    tenant_id = fulfillment.get("tenant_id")
    if type(tenant_id) is not str or not tenant_id.strip():
        _raise_validation_error("Tenant identity is required.", "fulfillment.tenant_id")

    _require_boolean(fulfillment, "offline", expected=True, path="fulfillment.offline")
    _require_boolean(
        fulfillment,
        "provisions_tenant",
        expected=False,
        path="fulfillment.provisions_tenant",
    )
    _require_boolean(
        fulfillment,
        "calls_license_server",
        expected=False,
        path="fulfillment.calls_license_server",
    )

    license_details = request.get("license")
    if type(license_details) is not dict:
        _raise_validation_error("License request details are required.", "license")
    _require_boolean(
        license_details,
        "secret_values_included",
        expected=False,
        path="license.secret_values_included",
    )


def canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def purchase_request_fingerprint(request: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(canonical_json(request).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _require_boolean(
    section: Mapping[str, Any],
    field: str,
    *,
    expected: bool,
    path: str,
) -> None:
    value = section.get(field)
    if type(value) is not bool or value is not expected:
        _raise_validation_error("Purchase request security declaration is invalid.", path)


def _raise_validation_error(message: str, path: str) -> None:
    raise EnterpriseFulfillmentError(message, context={"path": path})
