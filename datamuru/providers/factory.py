from __future__ import annotations

from datamuru.errors import ProviderError
from datamuru.providers.databricks.provider import DatabricksProvider
from datamuru.providers.snowflake.provider import SnowflakeProvider


def load_provider(project):
    provider_name = project.root.provider.name
    if provider_name == "databricks":
        return DatabricksProvider(project.provider_data)
    if provider_name == "snowflake":
        return SnowflakeProvider(project.provider_data)
    else:
        raise ProviderError(
            description=f"Unsupported provider: {provider_name}",
            context={"provider_name": provider_name},
            suggestion="Use databricks or snowflake, or install an Enterprise provider extension.",
        )
