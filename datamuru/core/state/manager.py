from __future__ import annotations

from pathlib import Path

from datamuru.core.config.models import LoadedProject
from datamuru.errors import StateBackendError

from .backends.local import LocalStateBackend


def resolve_state_backend(project: LoadedProject):
    backend = project.root.state.backend
    state_path = (project.root_path / project.root.state.path).resolve()
    if backend == "local":
        return LocalStateBackend(Path(state_path))
    raise StateBackendError(
        description=f"State backend '{backend}' is not implemented in the current alpha slice.",
        context={"backend": backend},
        suggestion="Use the local backend for now, or implement the cloud backend in DataMuru Enterprise.",
    )
