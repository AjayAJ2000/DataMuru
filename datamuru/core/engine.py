from __future__ import annotations

import json
from pathlib import Path

from datamuru.core.apply import apply_plan
from datamuru.core.config import load_project, resolve_environment_name, validate_project
from datamuru.core.importer import ImportEngine
from datamuru.core.plan import build_plan
from datamuru.core.state import resolve_state_backend
from datamuru.governance.masking import compile_masking_resources
from datamuru.governance.rbac import compile_rbac_resources
from datamuru.governance.taxonomy import compile_taxonomy_resources
from datamuru.errors import SavedPlanError
from datamuru.providers.factory import load_provider


class DataMuruEngine:
    def __init__(self, config_path: str | Path, environment: str | None = None) -> None:
        self.config_path = Path(config_path).resolve()
        self.environment = environment

    def validate(self):
        return validate_project(self.config_path)

    def _load(self):
        project = load_project(self.config_path)
        environment = resolve_environment_name(project, self.environment)
        provider = load_provider(project)
        state_backend = resolve_state_backend(project)
        return project, environment, provider, state_backend

    def plan(self, target: str | None = None):
        project, environment, provider, state_backend = self._load()
        state = state_backend.load()
        observed_state = provider.observe_current_state(project, environment)
        effective_state = state.merged_with(observed_state)
        desired_resources = provider.build_desired_resources(project)
        desired_resources.extend(compile_taxonomy_resources(project.governance))
        desired_resources.extend(compile_rbac_resources(project.governance))
        desired_resources.extend(compile_masking_resources(project.governance))
        return build_plan(
            environment=environment,
            desired_resources=desired_resources,
            current_state=effective_state,
            target=target,
        )

    def apply(self, target: str | None = None):
        _, _, provider, state_backend = self._load()
        plan = self.plan(target=target)
        return apply_plan(plan, provider, state_backend)

    def save_plan(self, output_path: str | Path, target: str | None = None) -> Path:
        plan = self.plan(target=target)
        resolved = Path(output_path).resolve()
        resolved.write_text(json.dumps(plan.to_dict(), indent=2), encoding="utf-8")
        return resolved

    def apply_saved_plan(self, plan_path: str | Path):
        _, _, provider, state_backend = self._load()
        resolved = Path(plan_path).resolve()
        if not resolved.exists():
            raise SavedPlanError(
                description=f"Saved plan file not found: {resolved}",
                context={"plan_path": str(resolved)},
            )
        loaded_plan = json.loads(resolved.read_text(encoding="utf-8"))
        from datamuru.types import Plan as SavedPlan  # local import to avoid circular feeling in bootstrap

        saved_plan = SavedPlan.from_dict(loaded_plan)
        return apply_plan(saved_plan, provider, state_backend)

    def edition_summary(self):
        project, _, _, _ = self._load()
        from datamuru.edition import EditionCatalog
        from datamuru.types import EditionSummary

        feature_map = project.root.features.model_dump(mode="python")
        definition = EditionCatalog.DEFINITIONS[project.root.project.edition]
        enabled_features = [name for name, enabled in feature_map.items() if enabled]
        restricted_features = sorted(
            feature_name for feature_name in EditionCatalog.ENTERPRISE_ONLY_FEATURES if feature_name not in definition.allowed_features
        )
        return EditionSummary(
            edition=project.root.project.edition,
            enabled_features=sorted(enabled_features),
            restricted_features=restricted_features,
        )

    def doctor(self):
        project, environment, provider, _ = self._load()
        return provider.doctor(project, environment)

    def import_discover(self, *, include_system: bool = False):
        return ImportEngine(config_path=self.config_path, environment=self.environment).discover(
            include_system=include_system
        )

    def import_generate(
        self,
        *,
        catalogs: list[str] | None = None,
        include_groups: bool = False,
        include_system: bool = False,
    ):
        return ImportEngine(config_path=self.config_path, environment=self.environment).generate(
            catalogs=catalogs,
            include_groups=include_groups,
            include_system=include_system,
        )

    def destroy(self, target: str | None = None):
        project, environment, _, state_backend = self._load()
        state_snapshot = state_backend.load()
        empty_plan = build_plan(
            environment=environment,
            desired_resources=[],
            current_state=state_snapshot,
            target=target,
        )
        provider = load_provider(project)
        return apply_plan(empty_plan, provider, state_backend)
