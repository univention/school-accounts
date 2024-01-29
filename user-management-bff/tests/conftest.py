# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import os

import pytest
from fastapi.testclient import TestClient

from user_management_bff.main import app


@pytest.fixture
def test_client(patch_env):
    with TestClient(app) as client:
        yield client


@pytest.fixture()
def api_prefix():
    return os.getenv("USER_MANAGEMENT__API_PREFIX", "")


@pytest.fixture()
def patch_env():
    _environ = os.environ.copy()
    os.environ["USER_MANAGEMENT__API_PREFIX"] = "/univention/ucsschool/user-management"
    os.environ["USER_MANAGEMENT__CORS__ALLOWED_ORIGINS"] = "*"
    yield
    os.environ.clear()
    os.environ.update(_environ)
