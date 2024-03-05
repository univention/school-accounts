# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Callable

import pytest
from authlib.integrations.requests_client import OAuth2Session


@pytest.fixture(scope="session")
def base_url(pytestconfig):
    return pytestconfig.getoption("base_url")


@pytest.fixture(scope="session", autouse=True)
def browser_context_args(browser_context_args):
    return {**browser_context_args, "ignore_https_errors": True}


@pytest.fixture
def access_token() -> Callable[[str, str], str]:
    def wrapper(username: str, password: str) -> str:
        client = OAuth2Session(client_id="ucsschool-user-management-test", client_secret="univention")
        token = client.fetch_token(
            "https://ucs-sso-ng.school.test/realms/ucs/protocol/openid-connect/token",
            username=username,
            password=password,
        )
        return token["access_token"]

    return wrapper
