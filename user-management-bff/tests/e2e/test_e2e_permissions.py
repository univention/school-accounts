# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import pytest
import requests


@pytest.mark.parametrize("username", ["mina.teacher", "max.student", "alex.admin"])
@pytest.mark.e2e
def test_user_read_self(access_token, base_url, username):
    token = access_token(username, "univention")
    response = requests.get(
        f"{base_url}/bff/users",
        params={"school": "school1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    user = next(user for user in response.json()["users"] if user["id"] == username)
    for attribute_name, attribute_value in user["attributes"].items():
        assert attribute_value["value"] is not None, attribute_name
        assert attribute_value["access"] in ("read",), attribute_name


@pytest.mark.parametrize(
    "username,read_access",
    [
        ("mina.teacher", True),
        ("max.student", True),
        ("alex.admin", False),
    ],
)
@pytest.mark.e2e
def test_teacher_read_test(access_token, base_url, username, read_access):
    token = access_token("mina.teacher", "univention")
    response = requests.get(
        f"{base_url}/bff/users",
        params={"school": "school1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    student = next(user for user in response.json()["users"] if user["id"] == username)
    for attribute_name, attribute_value in student["attributes"].items():
        assert (attribute_value["value"] is not None) == (
            read_access or attribute_name == "username"
        ), attribute_name
        assert (attribute_value["access"] == "read") == (
            read_access or attribute_name == "username"
        ), attribute_name


@pytest.mark.parametrize(
    "username,allowed_student,allowed_teacher,allowed_school_admin",
    [
        ("mina.teacher", False, False, False),
        ("max.student", False, False, False),
        ("alex.admin", True, True, False),
    ],
)
@pytest.mark.e2e
def test_delete_allowed_permission(
    access_token, base_url, username, allowed_student, allowed_teacher, allowed_school_admin
):
    token = access_token(username, "univention")
    response = requests.get(
        f"{base_url}/bff/users",
        params={"school": "school1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    test_mapping = {
        "mina.teacher": allowed_teacher,
        "max.student": allowed_student,
        "alex.admin": allowed_school_admin,
    }
    for user in response.json()["users"]:
        assert ("delete" in user["allowedActions"]) == test_mapping[user["id"]]


@pytest.mark.parametrize(
    "username,role,expected",
    [
        ("mina.teacher", "student", 403),
        ("mina.teacher", "teacher", 403),
        ("mina.teacher", "staff", 403),
        ("mina.teacher", "school_admin", 403),
        ("max.student", "student", 403),
        ("max.student", "teacher", 403),
        ("max.student", "staff", 403),
        ("max.student", "school_admin", 403),
        ("alex.admin", "student", 204),
        ("alex.admin", "teacher", 204),
        ("alex.admin", "staff", 204),
        ("alex.admin", "school_admin", 403),
    ],
)
@pytest.mark.asyncio
@pytest.mark.e2e
async def test_deletion(access_token, base_url, kelvin_user_factory, username, role, expected):
    token = access_token(username, "univention")
    user = await kelvin_user_factory(
        school="school1", schools=["school1"], roles=[role], school_classes={"school1": ["1a"]}
    )
    response = requests.delete(
        f"{base_url}/bff/users/{user.name}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == expected
