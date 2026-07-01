from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, Literal

from datamuru.enterprise.activation import LICENSE_SECRET_HANDLING
from datamuru.errors import EnterpriseFulfillmentError
from datamuru.modeling import DataMuruModel


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
        "connection_string",
        "dsn",
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


class FulfillmentDecision(DataMuruModel):
    schema_version: str
    generated_at: str
    decision_id: str
    decision_fingerprint: str
    decision: str
    operator: str
    decision_reference: str
    notes: str | None
    source_request_fingerprint: str
    tenant: dict[str, Any]
    commercial: dict[str, Any]
    entitlements: dict[str, list[str]]
    security: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="python")


class ActivationReceipt(DataMuruModel):
    schema_version: str
    generated_at: str
    receipt_id: str
    decision_id: str
    decision_fingerprint: str
    source_request_fingerprint: str
    tenant: dict[str, Any]
    entitlement: dict[str, Any]
    security: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="python")


class FulfillmentResult(DataMuruModel):
    decision: FulfillmentDecision
    receipt: ActivationReceipt | None
    decision_path: str
    receipt_path: str | None

    @property
    def decision_id(self) -> str:
        return self.decision.decision_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.to_dict(),
            "receipt": self.receipt.to_dict() if self.receipt else None,
            "decision_path": self.decision_path,
            "receipt_path": self.receipt_path,
        }


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
    for field in ("license_key_env", "license_key_present", "secret_handling"):
        if field not in license_details or not _is_valid_safe_secret_metadata(
            field, license_details[field]
        ):
            _raise_validation_error(
                "License request security metadata is invalid.",
                f"license.{field}",
            )
    _require_boolean(
        license_details,
        "secret_values_included",
        expected=False,
        path="license.secret_values_included",
    )
    if for_approval and license_details["license_key_present"] is not True:
        _raise_validation_error(
            "A present license key declaration is required for approval.",
            "license.license_key_present",
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


def build_fulfillment(
    request: Mapping[str, Any],
    *,
    decision: Literal["approve", "reject"],
    operator: str,
    decision_reference: str,
    notes: str | None = None,
    generated_at: datetime | None = None,
) -> tuple[FulfillmentDecision, ActivationReceipt | None]:
    if type(decision) is not str or decision not in {"approve", "reject"}:
        _raise_validation_error("Fulfillment decision must be approve or reject.", "decision")
    if type(operator) is not str or not operator.strip():
        _raise_validation_error("Fulfillment operator is required.", "operator")
    if type(decision_reference) is not str or not decision_reference.strip():
        _raise_validation_error("Fulfillment decision reference is required.", "decision_reference")
    if notes is not None and type(notes) is not str:
        _raise_validation_error("Fulfillment notes must be text.", "notes")

    validate_purchase_request(request, for_approval=decision == "approve")
    timestamp = (generated_at or datetime.now(UTC)).astimezone(UTC).replace(microsecond=0)
    generated_at_text = timestamp.isoformat().replace("+00:00", "Z")
    request_fingerprint = purchase_request_fingerprint(request)
    commercial = request["commercial"]
    fulfillment = request["fulfillment"]
    requested_entitlements = sorted(set(commercial["requested_entitlements"]))
    tenant = {
        "organization": commercial["organization"],
        "tenant_id": fulfillment["tenant_id"],
        "deployment_region": fulfillment.get("deployment_region"),
        "control_plane_url": fulfillment.get("control_plane_url"),
    }
    commercial_evidence = {
        "contact_email": commercial["contact_email"],
        "purchase_reference": commercial.get("purchase_reference"),
        "support_plan": commercial.get("support_plan"),
    }
    entitlement_evidence = {
        "requested": requested_entitlements,
        "approved": requested_entitlements if decision == "approve" else [],
        "rejected": requested_entitlements if decision == "reject" else [],
    }
    decision_identity = {
        "source_request_fingerprint": request_fingerprint,
        "decision": decision,
        "operator": operator.strip(),
        "decision_reference": decision_reference.strip(),
        "tenant": tenant,
        "commercial": commercial_evidence,
        "entitlements": entitlement_evidence,
    }
    decision_id_digest = _sha256(decision_identity)
    security = _security_posture()
    decision_payload = {
        "schema_version": "datamuru.enterprise_fulfillment_decision.v1",
        "generated_at": generated_at_text,
        "decision_id": f"fdr_{decision_id_digest[:20]}",
        "decision": decision,
        "operator": operator.strip(),
        "decision_reference": decision_reference.strip(),
        "notes": notes.strip() if notes and notes.strip() else None,
        "source_request_fingerprint": request_fingerprint,
        "tenant": tenant,
        "commercial": commercial_evidence,
        "entitlements": entitlement_evidence,
        "security": security,
    }
    decision_fingerprint = f"sha256:{_sha256(decision_payload)}"
    decision_record = FulfillmentDecision(
        **decision_payload,
        decision_fingerprint=decision_fingerprint,
    )
    if decision == "reject":
        return decision_record, None

    receipt_identity = {
        "decision_id": decision_record.decision_id,
        "source_request_fingerprint": request_fingerprint,
        "tenant": tenant,
        "enabled_features": requested_entitlements,
    }
    receipt_digest = _sha256(receipt_identity)
    receipt = ActivationReceipt(
        schema_version="datamuru.enterprise_activation_receipt.v1",
        generated_at=generated_at_text,
        receipt_id=f"far_{receipt_digest[:20]}",
        decision_id=decision_record.decision_id,
        decision_fingerprint=decision_record.decision_fingerprint,
        source_request_fingerprint=request_fingerprint,
        tenant=tenant,
        entitlement={
            "enabled_features": requested_entitlements,
            "support_plan": commercial.get("support_plan"),
            "purchase_reference": commercial.get("purchase_reference"),
        },
        security=security,
    )
    return decision_record, receipt


def write_fulfillment(
    request_path: str | Path,
    output_dir: str | Path,
    *,
    decision: Literal["approve", "reject"],
    operator: str,
    decision_reference: str,
    notes: str | None = None,
    generated_at: datetime | None = None,
) -> FulfillmentResult:
    request = load_purchase_request(request_path)
    decision_record, receipt = build_fulfillment(
        request,
        decision=decision,
        operator=operator,
        decision_reference=decision_reference,
        notes=notes,
        generated_at=generated_at,
    )
    resolved_dir = Path(output_dir).resolve()
    decision_path = resolved_dir / "fulfillment-decision.json"
    receipt_path = resolved_dir / "activation-receipt.json"
    decision_text = json.dumps(decision_record.to_dict(), indent=2) + "\n"
    receipt_text = json.dumps(receipt.to_dict(), indent=2) + "\n" if receipt else None

    expected_files = {decision_path.name: decision_text}
    if receipt_text is not None:
        expected_files[receipt_path.name] = receipt_text

    if resolved_dir.exists():
        if not resolved_dir.is_dir():
            _raise_validation_error(
                "Fulfillment output conflicts with existing evidence.",
                "output",
            )
        try:
            existing_names = {entry.name for entry in resolved_dir.iterdir()}
        except OSError as exc:
            raise EnterpriseFulfillmentError(
                "Existing fulfillment evidence could not be read.",
                context={"path": "output"},
            ) from exc
        if existing_names != set(expected_files):
            _raise_validation_error(
                "Fulfillment output conflicts with existing evidence.",
                "output",
            )
        for name, expected_text in expected_files.items():
            try:
                existing_text = (resolved_dir / name).read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise EnterpriseFulfillmentError(
                    "Existing fulfillment evidence could not be read.",
                    context={"path": "output"},
                ) from exc
            if existing_text != expected_text:
                _raise_validation_error(
                    "Fulfillment output conflicts with existing evidence.",
                    "output",
                )
    else:
        staging_dir: Path | None = None
        try:
            resolved_dir.parent.mkdir(parents=True, exist_ok=True)
            staging_dir = Path(
                tempfile.mkdtemp(
                    prefix=f".{resolved_dir.name}.",
                    suffix=".tmp",
                    dir=resolved_dir.parent,
                )
            )
            for name, expected_text in expected_files.items():
                _write_staged_file(staging_dir / name, expected_text)
            os.rename(staging_dir, resolved_dir)
            staging_dir = None
        except OSError as exc:
            raise EnterpriseFulfillmentError(
                "Fulfillment evidence could not be written without conflict.",
                context={"path": "output"},
            ) from exc
        finally:
            if staging_dir is not None:
                shutil.rmtree(staging_dir, ignore_errors=True)

    return FulfillmentResult(
        decision=decision_record,
        receipt=receipt,
        decision_path=str(decision_path),
        receipt_path=str(receipt_path) if receipt else None,
    )


def _write_staged_file(destination: Path, content: str) -> None:
    with destination.open(mode="w", encoding="utf-8", newline="") as staged_file:
        staged_file.write(content)
        staged_file.flush()
        os.fsync(staged_file.fileno())


def _sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _security_posture() -> dict[str, bool]:
    return {
        "offline": True,
        "payment_processed": False,
        "cryptographically_signed": False,
        "calls_license_server": False,
        "provisions_tenant": False,
        "secret_values_included": False,
    }


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
