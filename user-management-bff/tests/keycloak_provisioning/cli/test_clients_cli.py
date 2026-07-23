# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import json
import secrets

import pytest
from typer.testing import CliRunner

import keycloak_provisioning
from keycloak_provisioning.cli.clients import add, get_secret, modify
from keycloak_provisioning.cli.main import app
from keycloak_provisioning.keycloak import KeycloakClient, KeycloakClientError


class FileTextMock:
    def __init__(self, content: str):
        self.content = content

    def read(self):
        return self.content


@pytest.mark.parametrize("ignore_exists", [True, False])
def test_client_add(monkeypatch, mocker, ignore_exists):
    kc_client_mock = mocker.MagicMock(spec=KeycloakClient)
    ctx_mock = mocker.MagicMock()
    monkeypatch.setattr(
        keycloak_provisioning.cli.clients,
        "get_keycloak_client",
        lambda login_credentials: kc_client_mock,
    )
    add(ctx_mock, FileTextMock(json.dumps({"a": 1})), ignore_exists)
    kc_client_mock.create_client.assert_called_once_with({"a": 1}, ignore_exists=ignore_exists)


def test_client_get_secret(monkeypatch, mocker, capsys):
    kc_client_mock = mocker.MagicMock(spec=KeycloakClient)
    kc_client_mock.get_client_secret = mocker.Mock(return_value="SECRET")
    ctx_mock = mocker.MagicMock()
    monkeypatch.setattr(
        keycloak_provisioning.cli.clients,
        "get_keycloak_client",
        lambda login_credentials: kc_client_mock,
    )
    get_secret(ctx_mock, "test_id")
    captured = capsys.readouterr()
    assert captured.out == "SECRET\n"


def test_client_modify(monkeypatch, mocker):
    kc_client_mock = mocker.MagicMock(spec=KeycloakClient)
    ctx_mock = mocker.MagicMock()
    monkeypatch.setattr(
        keycloak_provisioning.cli.clients,
        "get_keycloak_client",
        lambda login_credentials: kc_client_mock,
    )
    modify(
        ctx_mock,
        "test_id",
        append_redirect_urls="new_server/path",
        remove_redirect_urls="old_server/path",
    )
    kc_client_mock.modify_client.assert_called_once_with(
        "test_id",
        append_redirect_urls="new_server/path",
        remove_redirect_urls="old_server/path",
    )


def test_client_add_overrides(monkeypatch, mocker):
    kc_client_mock = mocker.MagicMock(spec=KeycloakClient)
    ctx_mock = mocker.MagicMock()
    monkeypatch.setattr(
        keycloak_provisioning.cli.clients,
        "get_keycloak_client",
        lambda login_credentials: kc_client_mock,
    )
    monkeypatch.setattr(
        secrets,
        "token_urlsafe",
        lambda length: "0" * length,
    )
    add(
        ctx_mock,
        FileTextMock(json.dumps({"baseUrl": "BASE_URL", "secret": "secret", "a": 1})),
        home_url="OTHER_URL",
        create_secret=True,
    )
    kc_client_mock.create_client.assert_called_once_with(
        {
            "baseUrl": "OTHER_URL",
            "secret": "0" * 24,
            "a": 1,
        },
        ignore_exists=False,
    )


def test_client_add_invalid_json(mocker, monkeypatch, tmp_path):
    kc_client_mock = mocker.MagicMock(spec=KeycloakClient)
    monkeypatch.setattr(
        keycloak_provisioning.cli.clients,
        "get_keycloak_client",
        lambda login_credentials: kc_client_mock,
    )
    test_json = tmp_path / "test.json"
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
            "clients",
            "add",
            str(test_json.absolute()),
        ],
    )
    assert result.exit_code == 1
    assert "The provided client data is not a valid json file." in result.stdout


def test_client_add_kc_client_error(mocker, monkeypatch, tmp_path):
    kc_client_mock = mocker.MagicMock(spec=KeycloakClient)
    kc_client_mock.create_client = mocker.Mock(side_effect=KeycloakClientError("THIS IS THE MESSAGE"))
    monkeypatch.setattr(
        keycloak_provisioning.cli.clients,
        "get_keycloak_client",
        lambda login_credentials: kc_client_mock,
    )
    test_json = tmp_path / "test.json"
    test_json.write_text("{}")
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
            "clients",
            "add",
            str(test_json.absolute()),
        ],
    )
    assert result.exit_code == 1
    assert "Client creation failed with the following error: THIS IS THE MESSAGE" in result.stdout


def test_client_modify_kc_client_error(mocker, monkeypatch):
    kc_client_mock = mocker.MagicMock(spec=KeycloakClient)
    kc_client_mock.modify_client = mocker.Mock(side_effect=KeycloakClientError("THIS IS THE MESSAGE"))
    monkeypatch.setattr(
        keycloak_provisioning.cli.clients,
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
            "clients",
            "modify",
            "--append-redirect-urls",
            "new_server",
            "test_id",
        ],
    )
    assert result.exit_code == 1
    assert "Client modification failed with the following error: THIS IS THE MESSAGE" in result.stdout


def test_client_get_secret_kc_client_error(mocker, monkeypatch):
    kc_client_mock = mocker.MagicMock(spec=KeycloakClient)
    kc_client_mock.get_client_secret = mocker.Mock(
        side_effect=KeycloakClientError("THIS IS THE MESSAGE")
    )
    monkeypatch.setattr(
        keycloak_provisioning.cli.clients,
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
            "clients",
            "get-secret",
            "test_id",
        ],
    )
    assert result.exit_code == 1
    assert "Getting client secret failed with the following error: THIS IS THE MESSAGE" in result.stdout
