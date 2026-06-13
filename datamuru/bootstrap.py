from __future__ import annotations

import textwrap
from pathlib import Path


class ProjectScaffolder:
    def scaffold(
        self,
        output_dir: str | Path,
        *,
        name: str,
        provider: str = "databricks",
        cloud: str = "azure",
        edition: str = "open-source",
    ) -> list[Path]:
        root = Path(output_dir)
        created: list[Path] = []
        for relative in [
            Path("environments"),
            Path("providers"),
            Path("workspaces"),
            Path("governance"),
        ]:
            target = root / relative
            target.mkdir(parents=True, exist_ok=True)
            created.append(target)

        content = {
            root / "datamuru.yml": textwrap.dedent(
                f"""
                project:
                  name: {name}
                  version: "0.1.0"
                  description: "Bootstrap DataMuru project"
                  edition: {edition}
                  provider: {provider}

                environments:
                  - name: dev
                    config: ./environments/dev.yml

                default_environment: dev

                features:
                  governance: true
                  data_mesh: false
                  ingestion: false
                  modeling: false
                  observability: false
                  compliance_reporting: false
                  multi_workspace: false
                  hosted_control_plane: false
                  identity_management: false

                state:
                  backend: local
                  path: ./.datamuru/state-dev.json

                provider:
                  name: {provider}
                  cloud: {cloud}
                  config: ./providers/{provider}.yml
                """
            ).strip() + "\n",
            root / "environments" / "dev.yml": "environment:\n  name: dev\n",
            root / "providers" / f"{provider}.yml": textwrap.dedent(
                f"""
                provider:
                  cloud: {cloud}
                  connect_timeout_seconds: 10
                  credential_mode: personal-access-token
                  execution_mode: state-only
                  auth_type: pat
                  token_env: DATABRICKS_TOKEN
                  host: https://adb-placeholder.{cloud}.databricks.example
                """
            ).strip() + "\n",
            root / "workspaces" / "alpha-dev.yml": textwrap.dedent(
                f"""
                workspace:
                  name: alpha-dev
                  cloud: {cloud}
                  region: eastus2
                  catalogs:
                    - name: alpha_marketing
                      schemas:
                        - raw
                        - bronze
                        - silver
                        - gold
                """
            ).strip() + "\n",
            root / "governance" / "taxonomy.yml": textwrap.dedent(
                """
                taxonomy:
                  name: bootstrap
                  version: "0.1"
                  categories:
                    - id: internal
                      label: Internal
                      description: "Internal data"
                      handling:
                        retention_years: 3
                        encryption: at_rest
                """
            ).strip() + "\n",
            root / "governance" / "rbac.yml": textwrap.dedent(
                """
                rbac:
                  roles:
                    - id: data_consumer
                      name: Data Consumer
                      permissions:
                        - resource_type: schema
                          resource_pattern: "*.gold"
                          privilege: SELECT
                  assignments:
                    - principal: sample-consumers
                      type: group
                      roles:
                        - data_consumer
                      domains:
                        - alpha_marketing
                """
            ).strip() + "\n",
            root / "governance" / "masking.yml": textwrap.dedent(
                """
                masking:
                  builtins:
                    - id: partial_mask
                      description: Show last four characters for strings.
                      strategy: partial_mask
                """
            ).strip() + "\n",
        }
        for path, value in content.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(value, encoding="utf-8")
            created.append(path)
        return created
