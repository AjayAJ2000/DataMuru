from __future__ import annotations

from pathlib import Path

from datamuru.core.config.models import LoadedProject
from datamuru.errors import StateBackendError

from .backends.local import LocalStateBackend
from .inspection import inspect_state_backend


def resolve_state_backend(project: LoadedProject):
    backend = project.root.state.backend
    state_path = (project.root_path / project.root.state.path).resolve()
    if backend == "local":
        return LocalStateBackend(Path(state_path))
    report = inspect_state_backend(project)
    if report.remote:
        raise StateBackendError(
            description=(
                f"Remote state backend '{backend}' is a recognized hosted-workflow contract, "
                "but this OSS runtime cannot plan, apply, adopt, or destroy against it yet."
            ),
            code="DMR-STATE-REMOTE",
            context={
                "backend": report.backend,
                "location": report.location,
                "remote": report.remote,
                "runtime_supported": report.runtime_supported,
                "mode": report.mode,
                "checks": [check.to_dict() for check in report.checks],
            },
            suggestion=(
                "Run `datamuru state inspect` for readiness details, use local state for OSS "
                "plan/apply workflows, or route this project through a hosted control plane "
                "or Enterprise state extension."
            ),
        )
    raise StateBackendError(
        description=f"State backend '{backend}' is not implemented in the current alpha slice.",
        context={
            "backend": report.backend,
            "location": report.location,
            "runtime_supported": report.runtime_supported,
            "mode": report.mode,
            "checks": [check.to_dict() for check in report.checks],
        },
        suggestion="Use the local backend for now, or implement the backend in DataMuru Enterprise.",
    )
