# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import os
from typing import Any

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
    os.environ["USER_MANAGEMENT__ADAPTER__AUTHENTICATION"] = (
        "user_management_bff.adapters.authentication:AlwaysAuthenticatedAdapter"
    )
    os.environ["FILE_SCHOOLS_PERSISTENCE_ADAPTER__SOURCE"] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "../../dev/data/schools.json"
    )
    yield
    os.environ.clear()
    os.environ.update(_environ)


@pytest.fixture
def transform_user_dict_to_api_users_dict():
    def _transform_user_dict_to_api_users_dict(user_dict: dict[str, Any]) -> dict[str, Any]:
        transformed = {**user_dict}
        transformed["attributes"]["activated"] = not user_dict["attributes"]["disabled"]
        transformed["attributes"]["classes"] = [
            f"{school}:{school_class}"
            for school, school_classes in user_dict["attributes"]["school_classes"].items()
            for school_class in school_classes
        ]
        del transformed["attributes"]["school_classes"]
        del transformed["attributes"]["disabled"]
        return transformed

    return _transform_user_dict_to_api_users_dict
