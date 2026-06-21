from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import Field

from datamuru.modeling import DataMuruModel

if TYPE_CHECKING:
    from datamuru.core.config.models import LoadedProject


REMOTE_BACKENDS = {"s3", "azure_blob", "gcs"}


class StateBackendCheck(DataMuruModel):
    level: str
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return self.model_dump(mode="python")


class StateBackendReport(DataMuruModel):
    backend: str
    location: str
    resolved_location: str | None = None
    remote: bool
    runtime_supported: bool
    mode: str
    checks: list[StateBackendCheck] = Field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.runtime_supported and not any(check.level == "error" for check in self.checks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "location": self.location,
            "resolved_location": self.resolved_location,
            "remote": self.remote,
            "runtime_supported": self.runtime_supported,
            "mode": self.mode,
            "success": self.success,
            "checks": [check.to_dict() for check in self.checks],
        }


def inspect_state_backend(project: LoadedProject) -> StateBackendReport:
    backend = project.root.state.backend
    location = project.root.state.path
    if backend == "local":
        resolved = (project.root_path / location).resolve()
        checks = [
            StateBackendCheck(
                level="ok",
                code="state.local.supported",
                message="Local JSON state is supported in the OSS runtime.",
            )
        ]
        if not _is_relative_to(resolved, project.root_path.resolve()):
            checks.append(
                StateBackendCheck(
                    level="warning",
                    code="state.local.outside_project",
                    message="State path resolves outside the project root; protect it with the same care as project state.",
                )
            )
        return StateBackendReport(
            backend=backend,
            location=location,
            resolved_location=str(resolved),
            remote=False,
            runtime_supported=True,
            mode="read-write",
            checks=checks,
        )

    if backend in REMOTE_BACKENDS:
        return StateBackendReport(
            backend=backend,
            location=location,
            resolved_location=None,
            remote=True,
            runtime_supported=False,
            mode="contract-only",
            checks=[
                StateBackendCheck(
                    level="error",
                    code=f"state.{backend}.not_implemented",
                    message=(
                        f"Remote state backend '{backend}' is recognized as a configuration contract, "
                        "but this OSS runtime does not read or write it yet."
                    ),
                ),
                StateBackendCheck(
                    level="warning",
                    code="state.remote.hosted_boundary",
                    message=(
                        "Use a hosted control plane or Enterprise state extension for multi-user execution; "
                        "keep OSS plan/apply on local state until that boundary is available."
                    ),
                ),
            ],
        )

    return StateBackendReport(
        backend=backend,
        location=location,
        resolved_location=None,
        remote=False,
        runtime_supported=False,
        mode="unsupported",
        checks=[
            StateBackendCheck(
                level="error",
                code="state.backend.unsupported",
                message=f"State backend '{backend}' is not recognized.",
            )
        ],
    )


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
