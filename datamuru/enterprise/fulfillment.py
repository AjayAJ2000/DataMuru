from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from datamuru.enterprise.activation import LICENSE_SECRET_HANDLING
from datamuru.errors import EnterpriseFulfillmentError


PURCHASE_REQUEST_SCHEMA = "datamuru.enterprise_purchase_request.v1"
SUPPORTED_PURCHASE_REQUEST_SCHEMAS = frozenset({PURCHASE_REQUEST_SCHEMA})
SAFE_SECRET_METADATA_KEYS = frozenset(
    {
        "license_key_env",
        "license_key_present",
        "secret_values_included",
        "secret_handling",
    }
)
SECRET_KEY_NAMES = frozenset(
    {
        "credential",
        "credentials",
        "authorization",
        "auth_header",
        "bearer",
        "cookie",
        "session_cookie",
        "password",
        "passphrase",
        "secret",
        "secret_value",
        "token",
        "token_value",
        "raw_token",
        "refresh_token",
        "access_token",
        "id_token",
        "client_secret",
        "private_key",
        "access_key",
        "secret_access_key",
        "aws_secret_access_key",
        "api_key",
        "license_key",
    }
)
SECRET_KEY_SUFFIXES = (
    "_password",
    "_passphrase",
    "_secret",
    "_token",
    "_private_key",
    "_access_key",
    "_api_key",
    "_license_key",
    "_authorization",
    "_cookie",
)
ENVIRONMENT_VARIABLE_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
ACRONYM_KEY_BOUNDARY = re.compile(r"(?<=[A-Z])(?=[A-Z][a-z])")
CAMEL_KEY_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
NON_ALPHANUMERIC_KEY_CHARS = re.compile(r"[^A-Za-z0-9]+")


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

    if not isinstance(request, Mapping):
        _raise_validation_error("Purchase request must be a JSON object.", "request")

    validate_purchase_request(request, for_approval=False)
    return request


def validate_purchase_request(
    request: Mapping[str, Any],
    *,
    for_approval: bool,
) -> None:
    if not isinstance(request, Mapping):
        _raise_validation_error("Purchase request must be a JSON object.", "request")
    if type(for_approval) is not bool:
        _raise_validation_error("Approval validation mode must be a boolean.", "for_approval")

    if _contains_secret_bearing_key(request):
        _raise_validation_error("Purchase request contains a credential-bearing field.", "request")

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
    if not isinstance(report, Mapping):
        _raise_validation_error("Purchase request report is required.", "report")
    if for_approval and (not report or report.get("ready") is not True):
        _raise_validation_error("Purchase request report is not ready for approval.", "report.ready")

    commercial = request.get("commercial")
    if not isinstance(commercial, Mapping):
        _raise_validation_error("Commercial request details are required.", "commercial")

    for field in ("organization", "contact_email"):
        value = commercial.get(field)
        if type(value) is not str or not value.strip():
            _raise_validation_error("Commercial identifier is required.", f"commercial.{field}")

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
    if not isinstance(fulfillment, Mapping):
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
    if not isinstance(license_details, Mapping):
        _raise_validation_error("License request details are required.", "license")
    _require_boolean(
        license_details,
        "secret_values_included",
        expected=False,
        path="license.secret_values_included",
    )


def canonical_json(payload: Mapping[str, Any]) -> str:
    try:
        return json.dumps(
            _json_compatible(payload),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError, RecursionError) as exc:
        raise EnterpriseFulfillmentError(
            "Canonical JSON contains unsupported values.",
            context={"path": "payload"},
        ) from exc


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


def _contains_secret_bearing_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is str:
                normalized_key = _normalize_key(key)
                if normalized_key in SAFE_SECRET_METADATA_KEYS:
                    if not _is_valid_safe_secret_metadata(normalized_key, item):
                        return True
                elif _is_secret_bearing_key(normalized_key):
                    return True
            if _contains_secret_bearing_key(item):
                return True
        return False
    if isinstance(value, (list, tuple)):
        return any(_contains_secret_bearing_key(item) for item in value)
    return False


def _normalize_key(key: str) -> str:
    normalized = ACRONYM_KEY_BOUNDARY.sub("_", key)
    normalized = CAMEL_KEY_BOUNDARY.sub("_", normalized)
    return NON_ALPHANUMERIC_KEY_CHARS.sub("_", normalized).strip("_").casefold()


def _is_secret_bearing_key(normalized_key: str) -> bool:
    return normalized_key in SECRET_KEY_NAMES or normalized_key.endswith(SECRET_KEY_SUFFIXES)


def _is_valid_safe_secret_metadata(key: str, value: Any) -> bool:
    if key == "license_key_env":
        if type(value) is not str or ENVIRONMENT_VARIABLE_NAME.fullmatch(value) is None:
            return False
        name_parts = _normalize_key(value).split("_")
        return "license" in name_parts and "key" in name_parts
    if key == "license_key_present":
        return type(value) is bool
    if key == "secret_values_included":
        return value is False
    if key == "secret_handling":
        return type(value) is str and value == LICENSE_SECRET_HANDLING
    return False


def _json_compatible(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _json_compatible(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_compatible(item) for item in value]
    if isinstance(value, tuple):
        return [_json_compatible(item) for item in value]
    return value


def _raise_validation_error(message: str, path: str) -> None:
    raise EnterpriseFulfillmentError(message, context={"path": path})
