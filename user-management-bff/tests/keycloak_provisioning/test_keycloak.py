# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import pytest
from keycloak import KeycloakAdmin, KeycloakError, KeycloakOpenIDConnection, KeycloakPostError

import keycloak_provisioning.keycloak
from keycloak_provisioning.keycloak import KeycloakClient, KeycloakClientError, get_keycloak_client
from keycloak_provisioning.models import LoginCredentials


class TestKeycloakClient:
    @pytest.fixture
    def client_instance(self, mocker, monkeypatch):
        kc_oidc_mock = mocker.Mock(spec=KeycloakOpenIDConnection)
        kc_admin_mock = mocker.Mock(spec=KeycloakAdmin)
        monkeypatch.setattr(keycloak_provisioning.keycloak, "KeycloakOpenIDConnection", kc_oidc_mock)
        monkeypatch.setattr(keycloak_provisioning.keycloak, "KeycloakAdmin", kc_admin_mock)
        return KeycloakClient(
            LoginCredentials(username="user", password="password", url="url", realm="realm")
        )

    def test_init_keycloak_error(self, mocker, monkeypatch):
        connect_mock = mocker.Mock(side_effect=KeycloakError("THIS IS THE MESSAGE!"))
        monkeypatch.setattr(keycloak_provisioning.keycloak.KeycloakClient, "connect", connect_mock)
        with pytest.raises(KeycloakClientError, match="THIS IS THE MESSAGE!"):
            KeycloakClient(
                LoginCredentials(username="user", password="password", url="url", realm="realm")
            )

    def test__connect(self, mocker, monkeypatch):
        kc_oidc_mock = mocker.Mock()
        monkeypatch.setattr(keycloak_provisioning.keycloak, "KeycloakOpenIDConnection", kc_oidc_mock)
        KeycloakClient.connect(
            LoginCredentials(username="user", password="password", url="url", realm="realm")
        )
        kc_oidc_mock.assert_called_once_with(
            server_url="url",
            username="user",
            password="password",
            realm_name="realm",
            user_realm_name=None,
            verify=True,
        )

    @pytest.mark.parametrize("ignore_exists", [True, False])
    def test_create_realm(self, client_instance, ignore_exists):
        client_instance.create_realm("REALM", ignore_exists=ignore_exists)
        client_instance.keycloak_admin.create_realm.assert_called_once_with(
            payload={"realm": "REALM", "enabled": True},
            skip_exists=ignore_exists,
        )

    def test_create_realm_with_extra_data(self, client_instance):
        client_instance.create_realm("REALM", realm_data={"requiredActions": []})
        client_instance.keycloak_admin.create_realm.assert_called_once_with(
            payload={"realm": "REALM", "enabled": True, "requiredActions": []},
            skip_exists=False,
        )

    @pytest.mark.parametrize(
        "error,match",
        [
            (KeycloakPostError("invalid_json"), "Error creating realm."),
            (KeycloakPostError("{}"), "Error creating realm."),
            (KeycloakPostError('{"errorMessage": "THIS IS THE MESSAGE!"}'), "THIS IS THE MESSAGE!"),
            (KeycloakError("THIS IS THE MESSAGE!"), "THIS IS THE MESSAGE!"),
        ],
    )
    def test_create_realm_keycloak_error(self, client_instance, mocker, error, match):
        client_instance.keycloak_admin.create_realm = mocker.Mock(side_effect=error)
        with pytest.raises(KeycloakClientError, match=match):
            client_instance.create_realm("REALM")

    @pytest.mark.parametrize("ignore_exists", [True, False])
    def test_create_user(self, client_instance, ignore_exists):
        client_instance.create_user("username", "password", ignore_exists)

        client_instance.keycloak_admin.create_user.assert_called_once_with(
            payload={
                "username": "username",
                "enabled": True,
                "credentials": [{"value": "password", "type": "password"}],
            },
            exist_ok=ignore_exists,
        )

    @pytest.mark.parametrize(
        "error,match",
        [
            (KeycloakPostError("invalid_json"), "Error creating user."),
            (KeycloakPostError("{}"), "Error creating user."),
            (KeycloakPostError('{"errorMessage": "THIS IS THE MESSAGE!"}'), "THIS IS THE MESSAGE!"),
            (KeycloakError("THIS IS THE MESSAGE!"), "THIS IS THE MESSAGE!"),
        ],
    )
    def test_create_user_keycloak_error(self, client_instance, mocker, error, match):
        client_instance.keycloak_admin.create_user = mocker.Mock(side_effect=error)
        with pytest.raises(KeycloakClientError, match=match):
            client_instance.create_user("username", "password")

    @pytest.mark.parametrize("ignore_exists", [True, False])
    def test_create_client(self, client_instance, ignore_exists):
        client_instance.create_client({}, ignore_exists)
        client_instance.keycloak_admin.create_client.assert_called_once_with(
            payload={}, skip_exists=ignore_exists
        )

    @pytest.mark.parametrize(
        "error,match",
        [
            (KeycloakPostError("invalid_json"), "Error creating client."),
            (KeycloakPostError("{}"), "Error creating client."),
            (KeycloakPostError('{"errorMessage": "THIS IS THE MESSAGE!"}'), "THIS IS THE MESSAGE!"),
            (KeycloakError("THIS IS THE MESSAGE!"), "THIS IS THE MESSAGE!"),
        ],
    )
    def test_create_client_keycloak_error(self, client_instance, mocker, error, match):
        client_instance.keycloak_admin.create_client = mocker.Mock(side_effect=error)
        with pytest.raises(KeycloakClientError, match=match):
            client_instance.create_client({})


def test_get_keycloak_client(mocker, monkeypatch):
    kc_oidc_mock = mocker.Mock()
    kc_admin_mock = mocker.Mock()
    monkeypatch.setattr(keycloak_provisioning.keycloak, "KeycloakOpenIDConnection", kc_oidc_mock)
    monkeypatch.setattr(keycloak_provisioning.keycloak, "KeycloakAdmin", kc_admin_mock)
    result = get_keycloak_client(
        LoginCredentials(username="user", password="password", url="url", realm="realm")
    )
    assert isinstance(result, KeycloakClient)
