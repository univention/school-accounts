# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import pytest
import requests


@pytest.mark.parametrize(
    "username",
    [
        "mina.teacher",
        "max.student",
        pytest.param(
            "alex.admin", marks=[pytest.mark.xfail(reason="TBD: how to handle user without class?")]
        ),
    ],
)
@pytest.mark.e2e
def test_user_read_self(access_token, base_url, username):
    token = access_token(username, "univention")
    response = requests.get(
        f"{base_url}/bff/users",
        params={"school": "school1", "school_classes": "1a"},
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
        params={"school": "school1", "school_classes": "1a"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    try:
        user = next(user for user in response.json()["users"] if user["id"] == username)
    except StopIteration:
        if read_access:
            raise AssertionError("The user should be present, but is not!")
        else:
            return  # No permissions whatsoever means the user will not be present in the returned data.
    for attribute_name, attribute_value in user["attributes"].items():
        if attribute_name == "work_groups":
            continue
        assert (attribute_value["value"] is not None) == (
            read_access or attribute_name == "username"
        ), attribute_name
        assert (attribute_value["access"] == "read") == (
            read_access or attribute_name == "username"
        ), attribute_name


@pytest.mark.parametrize(
    "role,expected", [("teacher", 403), ("student", 200), ("school_admin", 403), ("staff", 403)]
)
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_teacher_set_password_on_role(
    access_token, base_url, kelvin_user_factory, faker, role, expected
):
    token = access_token("mina.teacher", "univention")
    user = await kelvin_user_factory(
        school="school1", schools=["school1"], roles=[role], school_classes={"school1": ["1a"]}
    )
    response = requests.patch(
        f"{base_url}/bff/users/{user.name}",
        headers={"Authorization": f"Bearer {token}"},
        params={"school": "school1"},
        json={"password": faker.password(length=10)},
    )
    assert response.status_code == expected


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_teacher_set_password_fail_in_other_school(
    access_token, base_url, kelvin_user_factory, faker
):
    token = access_token("mina.teacher", "univention")
    user = await kelvin_user_factory(
        school="school2", schools=["school2"], roles=["student"], school_classes={"school2": ["1a"]}
    )
    response = requests.patch(
        f"{base_url}/bff/users/{user.name}",
        headers={"Authorization": f"Bearer {token}"},
        params={"school": "school2"},
        json={"password": faker.password(length=10)},
    )
    assert response.status_code == 403


@pytest.mark.parametrize(
    "username,allowed_student,allowed_teacher,allowed_school_admin,allowed_staff",
    [
        ("mina.teacher", False, False, False, False),
        ("max.student", False, False, False, False),
        ("alex.admin", True, True, False, True),
        ("armin.staff", False, False, False, False),
    ],
)
@pytest.mark.e2e
def test_delete_allowed_permission(
    access_token,
    base_url,
    username,
    allowed_student,
    allowed_teacher,
    allowed_school_admin,
    allowed_staff,
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
        "armin.staff": allowed_staff,
    }
    for user in (user for user in response.json()["users"] if user["id"] in test_mapping):
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
