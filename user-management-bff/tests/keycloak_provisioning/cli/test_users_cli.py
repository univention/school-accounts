# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import pytest
from typer.testing import CliRunner

import keycloak_provisioning
from keycloak_provisioning.cli.main import app
from keycloak_provisioning.cli.users import add
from keycloak_provisioning.keycloak import KeycloakClient, KeycloakClientError


@pytest.mark.parametrize("ignore_exists", [True, False])
def test_user_add(monkeypatch, mocker, ignore_exists):
    kc_client_mock = mocker.MagicMock(spec=KeycloakClient)
    ctx_mock = mocker.MagicMock()
    monkeypatch.setattr(
        keycloak_provisioning.cli.users,
        "get_keycloak_client",
        lambda login_credentials: kc_client_mock,
    )
    add(ctx_mock, "username", "password", ignore_exists)
    kc_client_mock.create_user.assert_called_once_with(
        "username", "password", ignore_exists=ignore_exists
    )


def test_client_add_kc_client_error(mocker, monkeypatch):
    kc_client_mock = mocker.MagicMock(spec=KeycloakClient)
    kc_client_mock.create_user = mocker.Mock(side_effect=KeycloakClientError("THIS IS THE MESSAGE"))
    monkeypatch.setattr(
        keycloak_provisioning.cli.users,
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
            "users",
            "add",
            "username",
            "password",
        ],
    )
    assert result.exit_code == 1
    assert "User creation failed with the following error: THIS IS THE MESSAGE" in result.stdout
