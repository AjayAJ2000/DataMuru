from __future__ import annotations

from datamuru.errors import ProviderError
from datamuru.providers.databricks.provider import DatabricksProvider


def load_provider(project):
    provider_name = project.root.provider.name
    if provider_name != "databricks":
        raise ProviderError(
            description=f"Unsupported provider for alpha bootstrap: {provider_name}",
            context={"provider_name": provider_name},
        )
    return DatabricksProvider(project.provider_data)
