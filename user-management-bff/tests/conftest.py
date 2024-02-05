# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def test_client():
    from user_management_bff.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture
def api_prefix():
    return os.getenv("USER_MANAGEMENT__API_PREFIX", "")


@pytest.fixture(scope="session", autouse=True)
def patch_env():
    _environ = os.environ.copy()
    os.environ["USER_MANAGEMENT__API_PREFIX"] = "/univention/ucsschool/user-management/bff"
    os.environ["USER_MANAGEMENT__CORS__ALLOWED_ORIGINS"] = "*"
    os.environ["USER_MANAGEMENT__ADAPTER__USERS_PERSISTENCE"] = (
        "user_management_bff.adapters.users:FileUsersPersistenceAdapter"
    )
    os.environ["USER_MANAGEMENT__ADAPTER__USERS_REPRESENTATION"] = (
        "user_management_bff.adapters.api:FastAPIUsersRepresentationAdapter"
    )
    os.environ["FILE_USERS_PERSISTENCE_ADAPTER__SOURCE"] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "../../dev/data/users.json"
    )
    os.environ["USER_MANAGEMENT__ADAPTER__SCHOOLS_PERSISTENCE"] = (
        "user_management_bff.adapters.schools:FileSchoolsPersistenceAdapter"
    )
    os.environ["USER_MANAGEMENT__ADAPTER__SCHOOLS_REPRESENTATION"] = (
        "user_management_bff.adapters.api:FastAPISchoolsRepresentationAdapter"
    )
    os.environ["FILE_SCHOOLS_PERSISTENCE_ADAPTER__SOURCE"] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "../../dev/data/schools.json"
    )
    yield
    os.environ.clear()
    os.environ.update(_environ)
