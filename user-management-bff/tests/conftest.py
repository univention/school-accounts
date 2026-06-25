# Copyright (C) 2026 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import os
import random
import re
from typing import Any, Optional

import nest_asyncio
import pytest
from fastapi.testclient import TestClient
from ucsschool.kelvin.client import UserResource

from user_management_bff.models import User, UserAttributes

nest_asyncio.apply()


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
    os.environ["USER_MANAGEMENT__ADAPTER__PERMISSIONS"] = (
        "user_management_bff.adapters.permissions:FilePermissionsAdapter"
    )
    os.environ["FILE_PERMISSIONS_ADAPTER__SOURCE"] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "../../dev/data/permissions.json"
    )
    os.environ["USER_MANAGEMENT__ADAPTER__SCHOOL_CLASSES_PERSISTENCE"] = (
        "user_management_bff.adapters.school_classes:FileSchoolClassesPersistenceAdapter"
    )
    os.environ["FILE_SCHOOL_CLASSES_PERSISTENCE_ADAPTER__SOURCE"] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "../../dev/data/school_classes.json"
    )
    os.environ["USER_MANAGEMENT__ADAPTER__SCHOOL_CLASSES_REPRESENTATION"] = (
        "user_management_bff.adapters.api:FastAPISchoolClassesRepresentationAdapter"
    )
    os.environ["USER_MANAGEMENT__ADAPTER__WORK_GROUPS_PERSISTENCE"] = (
        "user_management_bff.adapters.work_groups:FileWorkGroupsPersistenceAdapter"
    )
    os.environ["FILE_WORK_GROUPS_PERSISTENCE_ADAPTER__SOURCE"] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "../../dev/data/work_groups.json"
    )
    os.environ["USER_MANAGEMENT__ADAPTER__WORK_GROUPS_REPRESENTATION"] = (
        "user_management_bff.adapters.api:FastAPIWorkGroupsRepresentationAdapter"
    )
    os.environ["USER_MANAGEMENT__ADAPTER__ADD_CONFIG_REPRESENTATION"] = (
        "user_management_bff.adapters.api:FastAPIAddConfigRepresentationAdapter"
    )
    os.environ["USER_MANAGEMENT__ADAPTER__EDIT_CONFIG_REPRESENTATION"] = (
        "user_management_bff.adapters.api:FastAPIEditConfigRepresentationAdapter"
    )
    os.environ["USER_MANAGEMENT__ADAPTER__LIST_CONFIG_REPRESENTATION"] = (
        "user_management_bff.adapters.api:FastAPIListConfigRepresentationAdapter"
    )
    yield
    os.environ.clear()
    os.environ.update(_environ)


@pytest.fixture
def patch_test_env(monkeypatch):
    """Patch additional test-specific environment variables."""

    def _patch_test_env(new_env):
        for key, value in new_env.items():
            monkeypatch.setenv(key, value)

    return _patch_test_env


@pytest.fixture
def transform_user_dict_to_api_users_dict():
    def _school_id_to_display_name(school_id):
        return " ".join(re.split(r"(\d)", school_id.replace("_", " ").title())[:-1])

    def _transform_user_dict_to_api_users_dict(user_dict: dict[str, Any]) -> dict[str, Any]:
        transformed = {**user_dict}
        transformed["attributes"]["activated"] = (
            user_dict["attributes"].get("activated", None) or not user_dict["attributes"]["disabled"]
        )
        sclasses = []
        for school, school_classes in user_dict["attributes"]["school_classes"].items():
            school_display_name = _school_id_to_display_name(school)
            for school_class in school_classes:
                sclasses.append(f"{school_class} ({school_display_name})")
        transformed["attributes"]["classes"] = sclasses

        wgroups = []
        for school, work_groups in user_dict["attributes"]["work_groups"].items():
            school_display_name = _school_id_to_display_name(school)
            for work_group in work_groups:
                wgroups.append(f"{work_group} ({school_display_name})")
        transformed["attributes"]["work_groups"] = wgroups

        roles = []
        for role in transformed["attributes"]["roles"]:
            school_display_name = _school_id_to_display_name(role.rsplit(":", 1)[1])
            role_str = role.replace("_", " ").split(":", 1)[0].title()
            roles.append(f"{role_str} ({school_display_name})")
        transformed["attributes"]["roles"] = roles

        schools = []
        for school_id in transformed["attributes"]["schools"]:
            schools.append(_school_id_to_display_name(school_id))
        transformed["attributes"]["schools"] = schools

        del transformed["attributes"]["school_classes"]
        if "disabled" in transformed["attributes"]:
            del transformed["attributes"]["disabled"]
        return transformed

    return _transform_user_dict_to_api_users_dict


@pytest.fixture
def delete_user_kelvin():
    async def _delete_user_kelvin(username: str, kelvin_session) -> None:
        async with kelvin_session as session:
            user = await UserResource(session=session).get(name=username)
            await user.delete()

    return _delete_user_kelvin


@pytest.fixture
def users_json_path():
    return os.environ["FILE_USERS_PERSISTENCE_ADAPTER__SOURCE"]


@pytest.fixture
def restore_users_json(users_json_path):
    with open(users_json_path, "r") as file:
        data = file.read()
    yield
    with open(users_json_path, "w") as file:
        file.write(data)


@pytest.fixture
def generate_user(faker):
    def _generate_user(*, identifier: Optional[str] = None) -> User:
        schools = [faker.word() for _ in range(random.randint(1, 3))]
        return User(
            id=identifier if identifier else faker.word(),
            attributes=UserAttributes(
                last_name=faker.last_name(),
                first_name=faker.first_name(),
                username=faker.user_name(),
                disabled=faker.boolean(),
                schools=schools,
                school_classes={
                    school: [faker.word() for _ in range(random.randint(1, 3))] for school in schools
                },
                work_groups={
                    school: [faker.word() for _ in range(random.randint(0, 2))] for school in schools
                },
                roles=[
                    f"{role}:school:{school}"
                    for school in schools
                    for role in random.choices(
                        ["student", "teacher", "staff", "school_admin"], k=random.randint(1, 2)
                    )
                ],
                password=faker.password(),
            ),
        )

    return _generate_user
