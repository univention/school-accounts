# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import json
import warnings
from json import JSONDecodeError

from keycloak import KeycloakAdmin, KeycloakError, KeycloakOpenIDConnection, KeycloakPostError

from .models import LoginCredentials


class KeycloakClientError(Exception):
    def __init__(self, error_message=""):
        Exception.__init__(self, error_message)
        self.error_message = error_message


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

    def create_realm(self, realm_name: str, ignore_exists: bool = False):
        try:
            self.keycloak_admin.create_realm(
                payload={"realm": realm_name, "enabled": True}, skip_exists=ignore_exists
            )
        except KeycloakPostError as exc:
            try:
                raise KeycloakClientError(
                    json.loads(exc.error_message).get("errorMessage", "Error creating realm.")
                )
            except JSONDecodeError:
                raise KeycloakClientError("Error creating realm.")
        except KeycloakError as exc:
            raise KeycloakClientError(exc.error_message)

    def create_user(self, username: str, password: str, ignore_exists: bool = False):
        try:
            self.keycloak_admin.create_user(
                payload={
                    "username": username,
                    "enabled": True,
                    "credentials": [{"value": password, "type": "password"}],
                },
                exist_ok=ignore_exists,
            )
        except KeycloakPostError as exc:
            try:
                raise KeycloakClientError(
                    json.loads(exc.error_message).get("errorMessage", "Error creating user.")
                )
            except JSONDecodeError:
                raise KeycloakClientError("Error creating user.")
        except KeycloakError as exc:
            raise KeycloakClientError(exc.error_message)

    def create_client(self, client_data: dict, ignore_exists: bool = False):
        try:
            self.keycloak_admin.create_client(payload=client_data, skip_exists=ignore_exists)
        except KeycloakPostError as exc:
            try:
                raise KeycloakClientError(
                    json.loads(exc.error_message).get("errorMessage", "Error creating client.")
                )
            except JSONDecodeError:
                raise KeycloakClientError("Error creating client.")
        except KeycloakError as exc:
            raise KeycloakClientError(exc.error_message)


def get_keycloak_client(login_credentials: LoginCredentials) -> KeycloakClient:
    return KeycloakClient(login_credentials)
