# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
from copy import copy

import pytest
from keycloak import (
    KeycloakAdmin,
    KeycloakError,
    KeycloakGetError,
    KeycloakOpenIDConnection,
    KeycloakPostError,
    KeycloakPutError,
)
from pytest_mock import MockerFixture

import keycloak_provisioning.keycloak
from keycloak_provisioning.keycloak import KeycloakClient, KeycloakClientError, get_keycloak_client
from keycloak_provisioning.models import LoginCredentials


class TestKeycloakClient:
    @pytest.fixture
    def client_instance(self, mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch) -> KeycloakClient:
        kc_oidc_mock = mocker.Mock(spec=KeycloakOpenIDConnection)
        kc_admin_mock = mocker.Mock(spec=KeycloakAdmin)
        monkeypatch.setattr(keycloak_provisioning.keycloak, "KeycloakOpenIDConnection", kc_oidc_mock)
        monkeypatch.setattr(keycloak_provisioning.keycloak, "KeycloakAdmin", kc_admin_mock)
        return KeycloakClient(
            LoginCredentials(username="user", password="password", url="url", realm="realm")
        )

    def test_init_keycloak_error(self, mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch):
        connect_mock = mocker.Mock(side_effect=KeycloakError("THIS IS THE MESSAGE!"))
        monkeypatch.setattr(keycloak_provisioning.keycloak.KeycloakClient, "connect", connect_mock)
        with pytest.raises(KeycloakClientError, match="THIS IS THE MESSAGE!"):
            KeycloakClient(
                LoginCredentials(username="user", password="password", url="url", realm="realm")
            )

    def test__connect(self, mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch):
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
    def test_create_realm(self, client_instance: KeycloakClient, ignore_exists: bool):
        client_instance.create_realm("REALM", ignore_exists=ignore_exists)
        client_instance.keycloak_admin.create_realm.assert_called_once_with(
            payload={"realm": "REALM", "enabled": True},
            skip_exists=ignore_exists,
        )

    def test_create_realm_with_extra_data(self, client_instance: KeycloakClient):
        client_instance.create_realm("REALM", realm_data={"requiredActions": []})
        client_instance.keycloak_admin.create_realm.assert_called_once_with(
            payload={"realm": "REALM", "enabled": True, "requiredActions": []},
            skip_exists=False,
        )

    @pytest.mark.parametrize("ignore_exists", [True, False])
    def test_create_user(self, client_instance: KeycloakClient, ignore_exists: bool):
        client_instance.create_user("username", "password", ignore_exists)

        client_instance.keycloak_admin.create_user.assert_called_once_with(
            payload={
                "username": "username",
                "enabled": True,
                "credentials": [{"value": "password", "type": "password"}],
            },
            exist_ok=ignore_exists,
        )

    @pytest.mark.parametrize("ignore_exists", [True, False])
    def test_create_client(self, client_instance: KeycloakClient, ignore_exists: bool):
        client_instance.create_client({}, ignore_exists)
        client_instance.keycloak_admin.create_client.assert_called_once_with(
            payload={}, skip_exists=ignore_exists
        )

    def test_get_client_secret(self, client_instance: KeycloakClient, mocker: MockerFixture):
        client_instance.keycloak_admin.get_client_secrets = mocker.Mock(
            return_value={"type": "test", "value": "SECRET"}
        )
        assert client_instance.get_client_secret("test_id") == "SECRET"

    @pytest.mark.parametrize(
        "append_redirect_urls",
        [None, [], ["new_r"], ["duplicate_r"], ["duplicate_r", "new_r"], ["new_r1", "new_r2"]],
    )
    @pytest.mark.parametrize(
        "remove_redirect_urls",
        [None, [], ["old_r"], ["unknown_r"], ["unknown_r", "old_r"], ["old_r1", "old_r2"]],
    )
    def test_modify_client(
        self,
        mocker: MockerFixture,
        client_instance: KeycloakClient,
        append_redirect_urls: list[str] | None,
        remove_redirect_urls: list[str] | None,
    ):
        client_test_data = {
            "a": 1,
            "redirectUris": ["duplicate_r", "server_r", "old_r", "old_r1", "old_r2"],
        }
        client_instance.keycloak_admin.get_client = mocker.Mock(return_value=client_test_data)
        client_instance.keycloak_admin.get_client_id = mocker.Mock(return_value="test_id")
        client_instance.modify_client(
            "test_id",
            append_redirect_urls=append_redirect_urls,
            remove_redirect_urls=remove_redirect_urls,
        )
        updated_client_test_data = copy(client_test_data)
        if append_redirect_urls:
            updated_client_test_data["redirectUris"] = sorted(
                list(set(client_test_data["redirectUris"]).union(append_redirect_urls))
            )
        if remove_redirect_urls:
            updated_client_test_data["redirectUris"] = sorted(
                list(set(client_test_data["redirectUris"]).difference(remove_redirect_urls))
            )
        client_instance.keycloak_admin.update_client.assert_called_once_with(
            "test_id",
            payload=updated_client_test_data,
        )

    def test_modify_client_sets_the_secret_and_drops_public(
        self, mocker: MockerFixture, client_instance: KeycloakClient
    ):
        client_test_data: dict[str, object] = {"publicClient": True, "redirectUris": []}
        client_instance.keycloak_admin.get_client = mocker.Mock(return_value=client_test_data)
        client_instance.keycloak_admin.get_client_id = mocker.Mock(return_value="test_id")
        update_client = mocker.Mock()
        client_instance.keycloak_admin.update_client = update_client
        client_instance.modify_client("test_id", client_secret="SECRET")
        update_client.assert_called_once_with(
            "test_id",
            payload={"publicClient": False, "redirectUris": [], "secret": "SECRET"},
        )

    def test_modify_client_without_a_secret_leaves_the_client_public(
        self, mocker: MockerFixture, client_instance: KeycloakClient
    ):
        client_test_data: dict[str, object] = {"publicClient": True, "redirectUris": []}
        client_instance.keycloak_admin.get_client = mocker.Mock(return_value=client_test_data)
        client_instance.keycloak_admin.get_client_id = mocker.Mock(return_value="test_id")
        update_client = mocker.Mock()
        client_instance.keycloak_admin.update_client = update_client
        client_instance.modify_client("test_id")
        update_client.assert_called_once_with(
            "test_id",
            payload={"publicClient": True, "redirectUris": []},
        )


def test_get_keycloak_client(mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch):
    kc_oidc_mock = mocker.Mock()
    kc_admin_mock = mocker.Mock()
    monkeypatch.setattr(keycloak_provisioning.keycloak, "KeycloakOpenIDConnection", kc_oidc_mock)
    monkeypatch.setattr(keycloak_provisioning.keycloak, "KeycloakAdmin", kc_admin_mock)
    result = get_keycloak_client(
        LoginCredentials(username="user", password="password", url="url", realm="realm")
    )
    assert isinstance(result, KeycloakClient)


@pytest.mark.parametrize(
    "error,new_error,match",
    [
        (KeycloakPostError("invalid_json"), KeycloakPostError, "invalid_json"),
        (KeycloakPostError("{}"), KeycloakPostError, "{}"),
        (
            KeycloakPostError('{"error": "THIS IS THE MESSAGE!"}'),
            KeycloakClientError,
            "THIS IS THE MESSAGE!",
        ),
        (
            KeycloakGetError('{"error": "THIS IS THE MESSAGE!"}'),
            KeycloakClientError,
            "THIS IS THE MESSAGE!",
        ),
        (
            KeycloakPutError('{"error": "THIS IS THE MESSAGE!"}'),
            KeycloakClientError,
            "THIS IS THE MESSAGE!",
        ),
        (KeycloakError("THIS IS THE MESSAGE!"), KeycloakError, "THIS IS THE MESSAGE!"),
    ],
)
def test_convert_keycloak_error(error: KeycloakError, new_error: type[Exception], match: str):
    with pytest.raises(new_error, match=match):
        with keycloak_provisioning.keycloak.convert_keycloak_error():
            raise error
