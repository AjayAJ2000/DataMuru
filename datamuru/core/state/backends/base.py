from __future__ import annotations

from abc import ABC, abstractmethod

from datamuru.core.state.models import StateSnapshot


class StateBackend(ABC):
    @abstractmethod
    def load(self) -> StateSnapshot: ...

    @abstractmethod
    def save(self, state: StateSnapshot) -> None: ...
