from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any

from datamuru.core.config.models import LoadedProject
from datamuru.enterprise.activation import ActivationCheck, build_activation_report
from datamuru.modeling import DataMuruModel


ENTITLEMENT_FEATURES = (
    "hosted_control_plane",
    "identity_management",
    "multi_workspace",
    "compliance_reporting",
)


class TenantEntitlementRecord(DataMuruModel):
    schema_version: str
    generated_at: str
    status: str
    ready: bool
    record_id: str
    project: dict[str, Any]
    tenant: dict[str, Any]
    entitlement: dict[str, Any]
    source: dict[str, Any]
    checks: list[ActivationCheck]
    security: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "status": self.status,
            "ready": self.ready,
            "record_id": self.record_id,
            "project": self.project,
            "tenant": self.tenant,
            "entitlement": self.entitlement,
            "source": self.source,
            "checks": [check.to_dict() for check in self.checks],
            "security": self.security,
        }


def build_tenant_entitlement_record(
    project: LoadedProject,
    *,
    environ: Mapping[str, str] | None = None,
    generated_at: datetime | None = None,
) -> TenantEntitlementRecord:
    report = build_activation_report(project, environ=environ)
    timestamp = (generated_at or datetime.now(UTC)).astimezone(UTC).replace(microsecond=0)
    activation = report.payload["activation"]
    features = report.payload["features"]
    project_payload = {
        "name": report.payload["project"]["name"],
        "provider": report.payload["project"]["provider"],
        "default_environment": report.payload["project"]["default_environment"],
    }
    tenant = {
        "organization": activation.get("organization"),
        "tenant_id": activation.get("tenant_id"),
        "deployment_region": activation.get("deployment_region"),
        "control_plane_url": activation.get("control_plane_url"),
    }
    entitlement = {
        "support_plan": activation.get("support_plan"),
        "purchase_reference": activation.get("purchase_reference"),
        "enabled_features": sorted(name for name in ENTITLEMENT_FEATURES if features.get(name)),
        "license_key_env": activation.get("license_key_env"),
        "license_key_present": activation.get("license_key_present", False),
    }
    source = {
        "activation_schema_version": report.payload["schema_version"],
        "fingerprint_algorithm": "sha256",
        "fingerprint_scope": "stable_redacted_tenant_entitlement_v1",
    }

    return TenantEntitlementRecord(
        schema_version="datamuru.tenant_entitlement_record.v1",
        generated_at=timestamp.isoformat().replace("+00:00", "Z"),
        status="ready" if report.ready else "blocked",
        ready=report.ready,
        record_id=_record_id(project_payload, tenant, entitlement, source),
        project=project_payload,
        tenant=tenant,
        entitlement=entitlement,
        source=source,
        checks=report.checks,
        security={
            "offline": True,
            "provisions_tenant": False,
            "calls_license_server": False,
            "mutates_provider": False,
            "mutates_state": False,
            "secret_values_included": False,
        },
    )


def write_tenant_entitlement_record(record: TenantEntitlementRecord, output_path: str | Path) -> Path:
    resolved = Path(output_path).resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(record.to_dict(), indent=2) + "\n", encoding="utf-8")
    return resolved


def _record_id(
    project: dict[str, Any],
    tenant: dict[str, Any],
    entitlement: dict[str, Any],
    source: dict[str, Any],
) -> str:
    stable_entitlement = {key: value for key, value in entitlement.items() if key != "license_key_present"}
    canonical_payload = {
        "project": project,
        "tenant": tenant,
        "entitlement": stable_entitlement,
        "activation_schema_version": source["activation_schema_version"],
    }
    canonical_json = json.dumps(canonical_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
    return f"ter_{digest[:20]}"
