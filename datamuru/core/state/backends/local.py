from __future__ import annotations

import json
from pathlib import Path

from datamuru.core.state.models import StateSnapshot
from datamuru.errors import StateBackendError

from .base import StateBackend


class LocalStateBackend(StateBackend):
    def __init__(self, state_path: Path) -> None:
        self.state_path = state_path

    def load(self) -> StateSnapshot:
        if not self.state_path.exists():
            return StateSnapshot()
        try:
            with self.state_path.open("r", encoding="utf-8") as handle:
                raw = json.load(handle)
        except json.JSONDecodeError as exc:  # pragma: no cover - depends on corrupt state
            raise StateBackendError(
                description=f"State file at {self.state_path} is not valid JSON.",
                context={"state_path": str(self.state_path), "json_error": str(exc)},
            ) from exc
        return StateSnapshot.model_validate(raw)

    def save(self, state: StateSnapshot) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with self.state_path.open("w", encoding="utf-8") as handle:
            json.dump(state.to_dict(), handle, indent=2, sort_keys=True)
            handle.write("\n")
