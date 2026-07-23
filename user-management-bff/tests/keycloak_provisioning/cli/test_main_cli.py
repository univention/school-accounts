# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import keycloak_provisioning
from keycloak_provisioning.cli.main import main_callback, run_script
from keycloak_provisioning.models import ContextObject, LoginCredentials


def test_main_callback_ctx_obj_created(mocker):
    ctx_mock = mocker.Mock()
    main_callback(ctx_mock, "USERNAME", "PASSWORD", "URL", "REALM", "USER_REALM", True)
    assert ctx_mock.obj == ContextObject(
        login_credentials=LoginCredentials(
            username="USERNAME",
            password="PASSWORD",
            url="URL",
            realm="REALM",
            user_realm="USER_REALM",
            secure=True,
        )
    )


def test_main_callback_ctx_defaults(mocker):
    ctx_mock = mocker.Mock()
    main_callback(ctx_mock, "USERNAME", "PASSWORD", "URL")
    assert ctx_mock.obj == ContextObject(
        login_credentials=LoginCredentials(
            username="USERNAME",
            password="PASSWORD",
            url="URL",
            realm="ucs",
            user_realm=None,
            secure=True,
        )
    )


def test_run_scripts_calls_app(monkeypatch, mocker):
    app_mock = mocker.Mock()
    monkeypatch.setattr(keycloak_provisioning.cli.main, "app", app_mock)
    run_script()
    app_mock.assert_called_once()
