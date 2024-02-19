# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import json

import pytest
from typer.testing import CliRunner

import keycloak_provisioning
from keycloak_provisioning.cli.clients import add
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


def test_client_add_overrides(monkeypatch, mocker):
    kc_client_mock = mocker.MagicMock(spec=KeycloakClient)
    ctx_mock = mocker.MagicMock()
    monkeypatch.setattr(
        keycloak_provisioning.cli.clients,
        "get_keycloak_client",
        lambda login_credentials: kc_client_mock,
    )
    add(
        ctx_mock,
        FileTextMock(
            json.dumps({"rootUrl": "ROOT_URL", "webOrigins": [], "redirectUris": [], "secret": "secret"})
        ),
        override_root_url="OTHER_URL",
        override_secret="SECRET",
        override_redirect_urls=["REDIRECT1", "REDIRECT2"],
        override_web_origins=["WEB_ORIGIN1", "WEB_ORIGIN2"],
    )
    kc_client_mock.create_client.assert_called_once_with(
        {
            "rootUrl": "OTHER_URL",
            "webOrigins": ["WEB_ORIGIN1", "WEB_ORIGIN2"],
            "redirectUris": ["REDIRECT1", "REDIRECT2"],
            "secret": "SECRET",
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
