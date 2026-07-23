# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import pytest
from typer.testing import CliRunner

import keycloak_provisioning
from keycloak_provisioning.cli.main import app
from keycloak_provisioning.cli.realms import add
from keycloak_provisioning.keycloak import KeycloakClient, KeycloakClientError


@pytest.mark.parametrize("ignore_exists", [True, False])
def test_realm_add(monkeypatch, mocker, ignore_exists):
    kc_client_mock = mocker.MagicMock(spec=KeycloakClient)
    ctx_mock = mocker.MagicMock()
    monkeypatch.setattr(
        keycloak_provisioning.cli.realms,
        "get_keycloak_client",
        lambda login_credentials: kc_client_mock,
    )
    add(ctx_mock, "realm", ignore_exists=ignore_exists)
    kc_client_mock.create_realm.assert_called_once_with(
        "realm",
        ignore_exists=ignore_exists,
        realm_data={},
    )


def test_realm_add_with_extra_data(monkeypatch, mocker, tmp_path):
    kc_client_mock = mocker.MagicMock(spec=KeycloakClient)
    monkeypatch.setattr(
        keycloak_provisioning.cli.realms,
        "get_keycloak_client",
        lambda login_credentials: kc_client_mock,
    )
    test_json = tmp_path / "testRealm.json"
    test_json.write_text('{"requiredActions": []}')
    runner = CliRunner()
    runner.invoke(
        app,
        [
            "--username",
            "USERNAME",
            "--password",
            "PASSWORD",
            "--url",
            "URL",
            "realms",
            "add",
            "REALM",
            "--realm-data",
            str(test_json.absolute()),
        ],
    )
    kc_client_mock.create_realm.assert_called_once_with(
        "REALM",
        ignore_exists=False,
        realm_data={"requiredActions": []},
    )


def test_realm_add_invalid_json(mocker, monkeypatch, tmp_path):
    kc_client_mock = mocker.MagicMock(spec=KeycloakClient)
    monkeypatch.setattr(
        keycloak_provisioning.cli.realms,
        "get_keycloak_client",
        lambda login_credentials: kc_client_mock,
    )
    test_json = tmp_path / "testRealm.json"
    test_json.write_text("INVALID_JSON")
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "--username",
            "USERNAME",
            "--password",
            "PASSWORD",
            "--url",
            "URL",
            "realms",
            "add",
            "REALM",
            "--realm-data",
            str(test_json.absolute()),
        ],
    )
    assert result.exit_code == 1
    assert "The provided realm data is not a valid json file." in result.stdout


def test_realm_add_kc_client_error(mocker, monkeypatch):
    kc_client_mock = mocker.MagicMock(spec=KeycloakClient)
    kc_client_mock.create_realm = mocker.Mock(side_effect=KeycloakClientError("THIS IS THE MESSAGE"))
    monkeypatch.setattr(
        keycloak_provisioning.cli.realms,
        "get_keycloak_client",
        lambda login_credentials: kc_client_mock,
    )
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "--username",
            "USERNAME",
            "--password",
            "PASSWORD",
            "--url",
            "URL",
            "realms",
            "add",
            "REALM",
        ],
    )
    assert result.exit_code == 1
    assert "Realm creation failed with the following error: THIS IS THE MESSAGE" in result.stdout
