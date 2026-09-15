# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import json
import warnings
from contextlib import contextmanager
from json import JSONDecodeError
from typing import Any, Optional

from keycloak import (
    KeycloakAdmin,
    KeycloakError,
    KeycloakOpenIDConnection,
)
from w3lib.url import canonicalize_url

from .models import LoginCredentials


class KeycloakClientError(Exception):
    def __init__(self, error_message: str = ""):
        Exception.__init__(self, error_message)
        self.error_message = error_message


@contextmanager
def convert_keycloak_error():
    try:
        yield
    except KeycloakError as exc:
        try:
            raise KeycloakClientError(json.loads(exc.error_message)["error"])
        except (JSONDecodeError, KeyError):
            raise exc


class KeycloakClient:
    def __init__(self, login_credentials: LoginCredentials):
        try:
            self.keycloak_admin = KeycloakAdmin(connection=self.connect(login_credentials))
        except KeycloakError as exc:
            raise KeycloakClientError(exc.error_message)

    @staticmethod
    def connect(login_credentials: LoginCredentials):
        warnings.simplefilter("ignore")
        with warnings.catch_warnings():
            return KeycloakOpenIDConnection(
                server_url=login_credentials.url,
                username=login_credentials.username,
                password=login_credentials.password,
                realm_name=login_credentials.realm,
                user_realm_name=login_credentials.user_realm,
                verify=login_credentials.secure,
            )

    def create_realm(
        self,
        realm_name: str,
        ignore_exists: bool = False,
        realm_data: Optional[dict[str, Any]] = None,
    ):
        realm_data = realm_data or {}
        with convert_keycloak_error():
            self.keycloak_admin.create_realm(
                payload={"realm": realm_name, "enabled": True, **realm_data}, skip_exists=ignore_exists
            )

    def create_user(self, username: str, password: str, ignore_exists: bool = False):
        with convert_keycloak_error():
            self.keycloak_admin.create_user(
                payload={
                    "username": username,
                    "enabled": True,
                    "credentials": [{"value": password, "type": "password"}],
                },
                exist_ok=ignore_exists,
            )

    def create_client(self, client_data: dict[str, Any], ignore_exists: bool = False):
        with convert_keycloak_error():
            self.keycloak_admin.create_client(payload=client_data, skip_exists=ignore_exists)

    def __sorted_union_urls(self, urls: list[str], urls_append: list[str]):
        return sorted(list(set(urls).union(canonicalize_url(u) for u in urls_append)))

    def __sorted_difference_urls(self, urls: list[str], urls_remove: list[str]):
        return sorted(list(set(urls).difference(canonicalize_url(u) for u in urls_remove)))

    def modify_client(
        self,
        client_id: str,
        append_redirect_urls: Optional[list[str]] = None,
        remove_redirect_urls: Optional[list[str]] = None,
        client_secret: str | None = None,
    ):
        with convert_keycloak_error():
            internal_id = self.keycloak_admin.get_client_id(client_id)
            oidc_client = self.keycloak_admin.get_client(internal_id)
        if append_redirect_urls:
            oidc_client["redirectUris"] = self.__sorted_union_urls(
                oidc_client["redirectUris"], append_redirect_urls
            )
        if remove_redirect_urls:
            oidc_client["redirectUris"] = self.__sorted_difference_urls(
                oidc_client["redirectUris"], remove_redirect_urls
            )
        if client_secret:
            oidc_client["publicClient"] = False
            oidc_client["secret"] = client_secret
        with convert_keycloak_error():
            oidc_client = self.keycloak_admin.update_client(internal_id, payload=oidc_client)

    def get_client_secret(self, client_id: str) -> str | None:
        with convert_keycloak_error():
            internal_id = self.keycloak_admin.get_client_id(client_id)
            if not internal_id:
                raise KeycloakClientError(f"The client {client_id} does not exist.")
            oidc_client = self.keycloak_admin.get_client(internal_id)
        if oidc_client.get("publicClient"):
            return None
        return oidc_client.get("secret")


def get_keycloak_client(login_credentials: LoginCredentials) -> KeycloakClient:
    return KeycloakClient(login_credentials)
