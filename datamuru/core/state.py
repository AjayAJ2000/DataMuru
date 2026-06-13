from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class LocalStateBackend:
    def __init__(self, state_path: Path) -> None:
        self.state_path = state_path

    def load(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {"resources": {}}
        with self.state_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def save(self, state: dict[str, Any]) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with self.state_path.open("w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2, sort_keys=True)
            handle.write("\n")
