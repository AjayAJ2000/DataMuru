from __future__ import annotations

import time
from typing import Any
from urllib.parse import quote

import requests
from requests import JSONDecodeError as RequestsJSONDecodeError

from datamuru.errors import ProviderError
from datamuru.modeling import DataMuruModel

from .auth import DatabricksAuthConfig

try:  # pragma: no cover - optional dependency path
    from databricks.sdk import WorkspaceClient
except Exception:  # pragma: no cover - optional dependency path
    WorkspaceClient = None


class ConnectivityProbeResult(DataMuruModel):
    ok: bool
    code: str
    message: str
    current_user: str | None = None
    details: dict[str, Any] = {}
    level: str = "ok"


class IdentityCapabilityResult(DataMuruModel):
    supported: bool
    code: str
    message: str
    level: str
    status_code: int | None = None
    details: dict[str, Any] = {}


class DatabricksWorkspaceClient:
    ACCOUNT_SCIM_BASE = "/api/2.0/account/scim/v2"

    def __init__(self, auth: DatabricksAuthConfig) -> None:
        self.auth = auth

    def sdk_available(self) -> bool:
        return WorkspaceClient is not None

    def build_sdk_client(self):
        if WorkspaceClient is None:
            raise ProviderError(
                description="databricks-sdk is not installed in the current Python environment.",
                context={"dependency": "databricks-sdk"},
                suggestion="Install the package with `pip install 'datamuru[databricks]'`.",
            )
        if self.auth.auth_type in {"pat", "databricks-cli", "oauth"}:
            token = self.auth.resolve_token()
            if not token:
                raise ProviderError(
                    description="Databricks bearer authentication was requested but no token was found.",
                    context={
                        "auth_type": self.auth.auth_type,
                        "token_env": self.auth.token_env,
                        "profile": self.auth.profile,
                    },
                    suggestion="Set the token environment variable or configure a Databricks CLI profile.",
                )
            return WorkspaceClient(host=self.auth.host, token=token)
        return WorkspaceClient(host=self.auth.host)

    def probe_workspace(self) -> ConnectivityProbeResult:
        if not self.auth.supports_live_connectivity():
            return ConnectivityProbeResult(
                ok=False,
                level="warning",
                code="provider.connectivity",
                message="Live connectivity probe skipped because the configured authentication is not ready.",
                details={"auth_type": self.auth.auth_type, "execution_mode": self.auth.execution_mode},
            )

        if self.auth.auth_type not in {"pat", "databricks-cli", "oauth"}:
            return ConnectivityProbeResult(
                ok=False,
                level="warning",
                code="provider.connectivity",
                message="Live connectivity probe needs a bearer-token auth path in the current alpha slice.",
                details={"auth_type": self.auth.auth_type},
            )

        endpoint = f"{self.auth.host.rstrip('/')}/api/2.0/preview/scim/v2/Me"
        try:
            response = requests.get(
                endpoint,
                headers={**self.auth.workspace_headers(), "Accept": "application/json"},
                timeout=self.auth.connect_timeout_seconds,
            )
        except requests.RequestException as exc:
            return ConnectivityProbeResult(
                ok=False,
                level="error",
                code="provider.connectivity",
                message="Databricks workspace connectivity probe failed before the API responded.",
                details={"endpoint": endpoint, "error": str(exc)},
            )

        if response.status_code == 200:
            try:
                payload = response.json()
            except RequestsJSONDecodeError:
                fallback = self._probe_catalogs_endpoint()
                if fallback.ok:
                    return fallback
                return fallback
            current_user = payload.get("userName") or payload.get("id")
            return ConnectivityProbeResult(
                ok=True,
                level="ok",
                code="provider.connectivity",
                message="Databricks workspace connectivity probe succeeded.",
                current_user=current_user,
                details={"endpoint": endpoint},
            )
        if response.status_code in {401, 403}:
            return ConnectivityProbeResult(
                ok=False,
                level="error",
                code="provider.connectivity",
                message="Databricks rejected the connectivity probe credentials.",
                details={"endpoint": endpoint, "status_code": response.status_code},
            )
        return ConnectivityProbeResult(
            ok=False,
            level="warning",
            code="provider.connectivity",
            message="Databricks responded, but the connectivity probe did not succeed cleanly.",
            details={"endpoint": endpoint, "status_code": response.status_code},
        )

    def _probe_catalogs_endpoint(self) -> ConnectivityProbeResult:
        endpoint = f"{self.auth.host.rstrip('/')}/api/2.1/unity-catalog/catalogs"
        try:
            response = requests.get(
                endpoint,
                headers={**self.auth.workspace_headers(), "Accept": "application/json"},
                params={"max_results": 1},
                timeout=self.auth.connect_timeout_seconds,
            )
        except requests.RequestException as exc:
            return ConnectivityProbeResult(
                ok=False,
                level="error",
                code="provider.connectivity",
                message="Databricks connectivity probe failed on both SCIM and Unity Catalog endpoints.",
                details={"endpoint": endpoint, "error": str(exc)},
            )

        if response.status_code in {401, 403}:
            return ConnectivityProbeResult(
                ok=False,
                level="error",
                code="provider.connectivity",
                message="Databricks rejected the Unity Catalog connectivity probe credentials.",
                details={"endpoint": endpoint, "status_code": response.status_code},
            )

        if response.status_code != 200:
            return ConnectivityProbeResult(
                ok=False,
                level="warning",
                code="provider.connectivity",
                message="Databricks responded to the Unity Catalog probe, but not with a clean success.",
                details={"endpoint": endpoint, "status_code": response.status_code},
            )

        try:
            payload = response.json()
        except RequestsJSONDecodeError:
            content_type = response.headers.get("Content-Type", "")
            body_snippet = response.text.strip().replace("\r", " ").replace("\n", " ")[:240]
            return ConnectivityProbeResult(
                ok=False,
                level="error",
                code="provider.connectivity",
                message="Databricks returned a non-JSON response from both SCIM and Unity Catalog probes.",
                details={
                    "endpoint": endpoint,
                    "content_type": content_type,
                    "response_url": response.url,
                    "body_snippet": body_snippet,
                },
            )

        catalogs = payload.get("catalogs", [])
        return ConnectivityProbeResult(
            ok=True,
            level="ok",
            code="provider.connectivity",
            message="Databricks Unity Catalog connectivity probe succeeded.",
            details={"endpoint": endpoint, "catalog_count_sample": len(catalogs)},
        )

    def list_groups(self) -> list[str]:
        resources: list[str] = []
        start_index = 1
        count = 100
        while True:
            payload = self._get_json(
                "/api/2.0/preview/scim/v2/Groups",
                params={"startIndex": start_index, "count": count},
            )
            batch = payload.get("Resources", [])
            resources.extend(
                item.get("displayName") for item in batch if isinstance(item, dict) and item.get("displayName")
            )
            items_per_page = int(payload.get("itemsPerPage", 0) or 0)
            total_results = int(payload.get("totalResults", 0) or 0)
            if not items_per_page or start_index + items_per_page > total_results:
                break
            start_index += items_per_page
        return resources

    def probe_identity_management(self) -> IdentityCapabilityResult:
        path = f"{self.ACCOUNT_SCIM_BASE}/Groups"
        url = f"{self.auth.host.rstrip('/')}{path}"
        try:
            response = requests.get(
                url,
                headers={**self.auth.workspace_headers(), "Accept": "application/scim+json"},
                params={"startIndex": 1, "count": 1},
                timeout=self.auth.connect_timeout_seconds,
            )
        except requests.RequestException as exc:
            return IdentityCapabilityResult(
                supported=False,
                level="error",
                code="provider.identity_management",
                message="Databricks identity capability probe could not reach the account SCIM endpoint.",
                details={"endpoint": url, "error": str(exc)},
            )

        if response.status_code == 200:
            try:
                response.json()
            except RequestsJSONDecodeError:
                return IdentityCapabilityResult(
                    supported=False,
                    level="warning",
                    code="provider.identity_management",
                    message=(
                        "Databricks account SCIM returned a non-API response. "
                        "Identity management is unavailable for this workspace."
                    ),
                    status_code=response.status_code,
                    details={"endpoint": url, "response": response.text[:240]},
                )
            return IdentityCapabilityResult(
                supported=True,
                level="ok",
                code="provider.identity_management",
                message="Databricks account SCIM identity management is available.",
                status_code=response.status_code,
                details={"endpoint": url},
            )
        if response.status_code == 404:
            return IdentityCapabilityResult(
                supported=False,
                level="warning",
                code="provider.identity_management",
                message=(
                    "Databricks account SCIM identity management is unavailable. "
                    "This is expected in Databricks Free Edition."
                ),
                status_code=response.status_code,
                details={"endpoint": url},
            )
        if response.status_code in {401, 403}:
            return IdentityCapabilityResult(
                supported=False,
                level="error",
                code="provider.identity_management",
                message=(
                    "Databricks account SCIM is present, but the current principal is not authorized "
                    "to manage identities."
                ),
                status_code=response.status_code,
                details={"endpoint": url, "response": response.text[:240]},
            )
        return IdentityCapabilityResult(
            supported=False,
            level="warning",
            code="provider.identity_management",
            message="Databricks account SCIM returned an unsupported capability response.",
            status_code=response.status_code,
            details={"endpoint": url, "response": response.text[:240]},
        )

    def list_account_users(self) -> list[dict[str, Any]]:
        return self._scim_list("Users")

    def list_account_groups(self) -> list[dict[str, Any]]:
        return self._scim_list("Groups")

    def list_account_service_principals(self) -> list[dict[str, Any]]:
        return self._scim_list("ServicePrincipals")

    def create_account_user(self, *, email: str, display_name: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": email,
            "active": True,
        }
        if display_name:
            payload["displayName"] = display_name
        return self._scim_request("POST", "Users", payload=payload)

    def create_account_group(self, *, name: str) -> dict[str, Any]:
        return self._scim_request(
            "POST",
            "Groups",
            payload={
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                "displayName": name,
            },
        )

    def create_account_service_principal(
        self,
        *,
        name: str,
        application_id: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServicePrincipal"],
            "displayName": name,
            "active": True,
        }
        if application_id:
            payload["applicationId"] = application_id
        return self._scim_request("POST", "ServicePrincipals", payload=payload)

    def delete_account_identity(self, *, resource_type: str, resource_id: str) -> None:
        self._scim_request("DELETE", f"{resource_type}/{quote(resource_id, safe='')}")

    def add_group_member(self, *, group_id: str, member_id: str) -> dict[str, Any]:
        return self._patch_group_membership(group_id=group_id, member_id=member_id, operation="add")

    def remove_group_member(self, *, group_id: str, member_id: str) -> dict[str, Any]:
        return self._patch_group_membership(group_id=group_id, member_id=member_id, operation="remove")

    def find_account_user(self, email: str) -> dict[str, Any] | None:
        return self._find_scim_resource(self.list_account_users(), "userName", email)

    def find_account_group(self, name: str) -> dict[str, Any] | None:
        return self._find_scim_resource(self.list_account_groups(), "displayName", name)

    def find_account_service_principal(self, name: str) -> dict[str, Any] | None:
        return self._find_scim_resource(self.list_account_service_principals(), "displayName", name)

    def list_catalogs(self) -> list[str]:
        catalogs: list[str] = []
        next_page_token: str | None = None
        while True:
            params: dict[str, Any] = {"max_results": 0}
            if next_page_token:
                params["page_token"] = next_page_token
            payload = self._get_json("/api/2.1/unity-catalog/catalogs", params=params)
            catalogs.extend(
                item.get("name") for item in payload.get("catalogs", []) if isinstance(item, dict) and item.get("name")
            )
            next_page_token = payload.get("next_page_token")
            if not next_page_token:
                break
        return catalogs

    def list_schemas(self, catalog_name: str) -> list[str]:
        schemas: list[str] = []
        next_page_token: str | None = None
        while True:
            params: dict[str, Any] = {"catalog_name": catalog_name, "max_results": 0}
            if next_page_token:
                params["page_token"] = next_page_token
            payload = self._get_json("/api/2.1/unity-catalog/schemas", params=params)
            schemas.extend(
                item.get("name") for item in payload.get("schemas", []) if isinstance(item, dict) and item.get("name")
            )
            next_page_token = payload.get("next_page_token")
            if not next_page_token:
                break
        return schemas

    def create_catalog(self, name: str, *, managed_location: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": name}
        if managed_location:
            payload["storage_root"] = managed_location
        return self._post_json("/api/2.1/unity-catalog/catalogs", payload=payload)

    def create_catalog_with_default_storage(self, name: str) -> dict[str, Any]:
        statement = f"CREATE CATALOG IF NOT EXISTS {self._quote_sql_identifier(name)}"
        return self.execute_sql_statement(statement)

    def create_schema(
        self,
        catalog_name: str,
        schema_name: str,
        *,
        managed_location: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"catalog_name": catalog_name, "name": schema_name}
        if managed_location:
            payload["storage_root"] = managed_location
        return self._post_json("/api/2.1/unity-catalog/schemas", payload=payload)

    def grant_privilege(self, *, privilege: str, securable_type: str, securable_name: str, principal: str) -> dict[str, Any]:
        statement = (
            f"GRANT {privilege} ON {securable_type.upper()} "
            f"{self._quote_sql_object_name(securable_name)} TO {self._quote_sql_identifier(principal)}"
        )
        return self.execute_sql_statement(statement)

    def revoke_privilege(self, *, privilege: str, securable_type: str, securable_name: str, principal: str) -> dict[str, Any]:
        statement = (
            f"REVOKE {privilege} ON {securable_type.upper()} "
            f"{self._quote_sql_object_name(securable_name)} FROM {self._quote_sql_identifier(principal)}"
        )
        return self.execute_sql_statement(statement)

    def show_grants(self, *, securable_type: str, securable_name: str) -> list[dict[str, Any]]:
        statement = f"SHOW GRANTS ON {securable_type.upper()} {self._quote_sql_object_name(securable_name)}"
        rows = self.execute_sql_rows(statement)
        grants: list[dict[str, Any]] = []
        for row in rows:
            normalized = {self._normalize_key(key): value for key, value in row.items()}
            principal = self._first_present(
                normalized,
                "principal",
                "principalname",
                "grantee",
                "user",
            )
            privilege = self._first_present(
                normalized,
                "actiontype",
                "action_type",
                "privilege",
                "privilegetype",
                "grant",
            )
            object_name = self._first_present(
                normalized,
                "objectkey",
                "object_key",
                "objectname",
                "object_name",
                "name",
            )
            if not principal or not privilege:
                continue
            grants.append(
                {
                    "principal": str(principal),
                    "privilege": str(privilege).upper(),
                    "securable_type": securable_type.lower(),
                    "securable_name": str(object_name or securable_name),
                }
            )
        return grants

    def delete_catalog(self, name: str, *, force: bool = False) -> None:
        self._delete("/api/2.1/unity-catalog/catalogs/{name}".format(name=name), params={"force": str(force).lower()})

    def delete_schema(self, full_name: str, *, force: bool = False) -> None:
        self._delete(
            "/api/2.1/unity-catalog/schemas/{full_name}".format(full_name=full_name),
            params={"force": str(force).lower()},
        )

    def _get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        timeout_seconds: int | None = None,
    ) -> dict[str, Any]:
        if self.auth.auth_type not in {"pat", "databricks-cli", "oauth"}:
            raise ProviderError(
                description="Raw Databricks HTTPS calls require a bearer token in the current provider implementation.",
                context={"auth_type": self.auth.auth_type, "path": path},
                suggestion="Use PAT, Databricks CLI profile token auth, OAuth token auth, or an Enterprise auth extension.",
            )
        url = f"{self.auth.host.rstrip('/')}{path}"
        try:
            response = requests.get(
                url,
                headers={**self.auth.workspace_headers(), "Accept": "application/json"},
                params=params,
                timeout=timeout_seconds or self.auth.connect_timeout_seconds,
            )
            response.raise_for_status()
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            raise ProviderError(
                description="Databricks API request failed.",
                context={"url": url, "status_code": status_code, "response": exc.response.text if exc.response is not None else None},
                suggestion="Verify the PAT scopes, workspace URL, and object-level permissions.",
            ) from exc
        except requests.RequestException as exc:
            raise ProviderError(
                description="Databricks API request could not be completed.",
                context={"url": url, "error": str(exc)},
                suggestion="Verify workspace reachability and local network access.",
            ) from exc
        try:
            return response.json()
        except RequestsJSONDecodeError as exc:
            raise ProviderError(
                description="Databricks API request returned a non-JSON response.",
                context={
                    "url": url,
                    "content_type": response.headers.get("Content-Type", ""),
                    "response_snippet": response.text.strip().replace("\r", " ").replace("\n", " ")[:240],
                },
                suggestion="Verify the workspace host, token target, and whether the endpoint is available in this Databricks edition.",
            ) from exc

    def _scim_list(self, resource_type: str) -> list[dict[str, Any]]:
        resources: list[dict[str, Any]] = []
        start_index = 1
        count = 100
        while True:
            payload = self._scim_request(
                "GET",
                resource_type,
                params={"startIndex": start_index, "count": count},
            )
            batch = payload.get("Resources", [])
            resources.extend(item for item in batch if isinstance(item, dict))
            items_per_page = int(payload.get("itemsPerPage", 0) or 0)
            total_results = int(payload.get("totalResults", 0) or 0)
            if not items_per_page or start_index + items_per_page > total_results:
                break
            start_index += items_per_page
        return resources

    def _patch_group_membership(self, *, group_id: str, member_id: str, operation: str) -> dict[str, Any]:
        if operation == "add":
            operation_payload: dict[str, Any] = {
                "op": "add",
                "value": {"members": [{"value": member_id}]},
            }
        else:
            operation_payload = {
                "op": "remove",
                "path": f'members[value eq "{member_id}"]',
            }
        return self._scim_request(
            "PATCH",
            f"Groups/{quote(group_id, safe='')}",
            payload={
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
                "Operations": [operation_payload],
            },
        )

    def _scim_request(
        self,
        method: str,
        resource_path: str,
        *,
        payload: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.auth.host.rstrip('/')}{self.ACCOUNT_SCIM_BASE}/{resource_path.lstrip('/')}"
        headers = {
            **self.auth.workspace_headers(),
            "Accept": "application/scim+json",
            "Content-Type": "application/scim+json",
        }
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                json=payload,
                params=params,
                timeout=self.auth.connect_timeout_seconds,
            )
            if response.status_code not in {200, 201, 204}:
                response.raise_for_status()
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            raise ProviderError(
                description="Databricks account SCIM identity request failed.",
                context={
                    "method": method,
                    "url": url,
                    "status_code": status_code,
                    "response": exc.response.text if exc.response is not None else None,
                },
                suggestion=(
                    "Use a full Databricks workspace with account SCIM support and authenticate as an "
                    "account admin, workspace admin, or authorized group manager."
                ),
            ) from exc
        except requests.RequestException as exc:
            raise ProviderError(
                description="Databricks account SCIM identity request could not be completed.",
                context={"method": method, "url": url, "error": str(exc)},
                suggestion="Verify workspace connectivity and the configured identity administration endpoint.",
            ) from exc
        if response.status_code == 204 or not response.text:
            return {}
        try:
            return response.json()
        except RequestsJSONDecodeError as exc:
            raise ProviderError(
                description="Databricks account SCIM returned a non-JSON response.",
                context={"method": method, "url": url, "response": response.text[:240]},
            ) from exc

    @staticmethod
    def _find_scim_resource(
        resources: list[dict[str, Any]],
        key: str,
        expected: str,
    ) -> dict[str, Any] | None:
        expected_normalized = expected.casefold()
        return next(
            (
                resource
                for resource in resources
                if str(resource.get(key, "")).casefold() == expected_normalized
            ),
            None,
        )

    def execute_sql_statement(self, statement: str) -> dict[str, Any]:
        warehouse_id = self.auth.resolve_sql_warehouse_id()
        if not warehouse_id:
            raise ProviderError(
                description="Databricks SQL warehouse ID is required to execute SQL for default-storage catalog creation.",
                context={
                    "statement": statement,
                    "sql_warehouse_id": self.auth.sql_warehouse_id,
                    "sql_warehouse_id_env": self.auth.sql_warehouse_id_env,
                },
                suggestion=(
                    "Set `sql_warehouse_id` in providers/databricks.yml or point `sql_warehouse_id_env` "
                    "to an environment variable that contains the SQL warehouse ID."
                ),
            )
        payload = {
            "statement": statement,
            "warehouse_id": warehouse_id,
            "wait_timeout": "0s",
            "on_wait_timeout": "CONTINUE",
            "disposition": "INLINE",
            "format": "JSON_ARRAY",
        }
        response = self._post_json("/api/2.0/sql/statements", payload=payload)
        status = (response.get("status") or {}).get("state")
        statement_id = response.get("statement_id")
        if status == "SUCCEEDED":
            return response
        if statement_id:
            return self._poll_statement(statement_id=statement_id, statement=statement, warehouse_id=warehouse_id)
        self._raise_statement_failure(
            statement=statement,
            warehouse_id=warehouse_id,
            statement_id=statement_id,
            response=response,
        )
        return response

    def execute_sql_rows(self, statement: str) -> list[dict[str, Any]]:
        response = self.execute_sql_statement(statement)
        return self._extract_statement_rows(response)

    def _post_json(self, path: str, *, payload: dict[str, Any]) -> dict[str, Any]:
        if self.auth.auth_type not in {"pat", "databricks-cli", "oauth"}:
            raise ProviderError(
                description="Raw Databricks HTTPS calls require a bearer token in the current provider implementation.",
                context={"auth_type": self.auth.auth_type, "path": path},
                suggestion="Use PAT, Databricks CLI profile token auth, OAuth token auth, or an Enterprise auth extension.",
            )
        url = f"{self.auth.host.rstrip('/')}{path}"
        try:
            response = requests.post(
                url,
                headers={**self.auth.workspace_headers(), "Content-Type": "application/json"},
                json=payload,
                timeout=self.auth.connect_timeout_seconds,
            )
            if response.status_code not in {200, 201}:
                response.raise_for_status()
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            raise ProviderError(
                description="Databricks API create request failed.",
                context={
                    "url": url,
                    "payload": payload,
                    "status_code": status_code,
                    "response": exc.response.text if exc.response is not None else None,
                },
                suggestion="Verify Unity Catalog permissions and the target object name.",
            ) from exc
        except requests.RequestException as exc:
            raise ProviderError(
                description="Databricks API create request could not be completed.",
                context={"url": url, "payload": payload, "error": str(exc)},
                suggestion="Verify workspace reachability and local network access.",
            ) from exc
        return response.json() if response.text else {}

    def _poll_statement(self, *, statement_id: str, statement: str, warehouse_id: str) -> dict[str, Any]:
        last_response: dict[str, Any] | None = None
        poll_timeout_seconds = max(self.auth.connect_timeout_seconds, 30)
        for _ in range(20):
            response = self._get_json(
                f"/api/2.0/sql/statements/{statement_id}",
                timeout_seconds=poll_timeout_seconds,
            )
            last_response = response
            status = (response.get("status") or {}).get("state")
            if status == "SUCCEEDED":
                return response
            if status in {"FAILED", "CANCELED", "CLOSED"}:
                self._raise_statement_failure(
                    statement=statement,
                    warehouse_id=warehouse_id,
                    statement_id=statement_id,
                    response=response,
                )
            time.sleep(1)
        self._raise_statement_failure(
            statement=statement,
            warehouse_id=warehouse_id,
            statement_id=statement_id,
            response=last_response or {"status": {"state": "TIMED_OUT"}},
        )
        return {}

    def _delete(self, path: str, *, params: dict[str, Any] | None = None) -> None:
        if self.auth.auth_type not in {"pat", "databricks-cli", "oauth"}:
            raise ProviderError(
                description="Raw Databricks HTTPS calls require a bearer token in the current provider implementation.",
                context={"auth_type": self.auth.auth_type, "path": path},
                suggestion="Use PAT, Databricks CLI profile token auth, OAuth token auth, or an Enterprise auth extension.",
            )
        url = f"{self.auth.host.rstrip('/')}{path}"
        try:
            response = requests.delete(
                url,
                headers=self.auth.workspace_headers(),
                params=params,
                timeout=self.auth.connect_timeout_seconds,
            )
            if response.status_code not in {200, 204}:
                response.raise_for_status()
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            raise ProviderError(
                description="Databricks API delete request failed.",
                context={
                    "url": url,
                    "params": params,
                    "status_code": status_code,
                    "response": exc.response.text if exc.response is not None else None,
                },
                suggestion="Verify object ownership, dependencies, and Unity Catalog privileges.",
            ) from exc
        except requests.RequestException as exc:
            raise ProviderError(
                description="Databricks API delete request could not be completed.",
                context={"url": url, "params": params, "error": str(exc)},
                suggestion="Verify workspace reachability and local network access.",
            ) from exc

    @staticmethod
    def _quote_sql_identifier(value: str) -> str:
        return f"`{value.replace('`', '``')}`"

    @classmethod
    def _quote_sql_object_name(cls, value: str) -> str:
        return ".".join(cls._quote_sql_identifier(part) for part in value.split("."))

    def _raise_statement_failure(
        self,
        *,
        statement: str,
        warehouse_id: str,
        statement_id: str | None,
        response: dict[str, Any],
    ) -> None:
        status = response.get("status") or {}
        error = response.get("error") or {}
        raise ProviderError(
            description="Databricks SQL statement execution failed.",
            context={
                "statement": statement,
                "warehouse_id": warehouse_id,
                "statement_id": statement_id,
                "state": status.get("state"),
                "error_code": error.get("error_code"),
                "error_message": error.get("message"),
                "response": response,
            },
            suggestion=(
                "Verify the SQL warehouse ID, workspace SQL permissions, and whether the workspace supports "
                "default-storage catalog creation through SQL."
            ),
        )

    @staticmethod
    def _extract_statement_rows(response: dict[str, Any]) -> list[dict[str, Any]]:
        manifest = response.get("manifest") or {}
        result = response.get("result") or {}
        schema = manifest.get("schema") or result.get("schema") or {}
        columns = schema.get("columns") or schema.get("column_infos") or []
        column_names = [
            str(column.get("name") or column.get("field_name") or f"column_{index}")
            for index, column in enumerate(columns)
            if isinstance(column, dict)
        ]
        raw_rows = result.get("data_array") or response.get("data_array") or []
        rows: list[dict[str, Any]] = []
        for raw_row in raw_rows:
            if isinstance(raw_row, dict):
                rows.append(raw_row)
                continue
            if isinstance(raw_row, list):
                keys = column_names or [f"column_{index}" for index in range(len(raw_row))]
                rows.append(dict(zip(keys, raw_row, strict=False)))
        return rows

    @staticmethod
    def _normalize_key(value: str) -> str:
        return "".join(character for character in str(value).lower() if character.isalnum() or character == "_")

    @staticmethod
    def _first_present(values: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            if key in values and values[key] not in {None, ""}:
                return values[key]
        return None
