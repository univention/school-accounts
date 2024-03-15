# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import pytest
import requests


@pytest.mark.e2e
@pytest.mark.parametrize("username, password", [("alex.admin", "univention")])
@pytest.mark.asyncio
async def test_create_user_allowed(access_token, base_url, kelvin_user_deletion, username, password):
    token = access_token(username, password)
    user = {
        "first_name": "Max",
        "last_name": "Mustermann",
        "username": "max.mustermann",
        "roles": ["teacher"],
        "school": "school1",
        "school_classes": [],
        "disabled": False,
    }
    kelvin_user_deletion("max.mustermann")
    response = requests.post(
        f"{base_url}/bff/users", headers={"Authorization": f"Bearer {token}"}, json=user
    )
    assert response.status_code == 201, response.json()
    assert response.json() == {
        "user": {
            "id": "max.mustermann",
            "attributes": {
                "last_name": {"value": "Mustermann", "access": "write"},
                "first_name": {"value": "Max", "access": "write"},
                "username": {"value": "max.mustermann", "access": "write"},
                "activated": {"value": True, "access": "write"},
                "schools": {"value": ["school1"], "access": "write"},
                "classes": {"value": [], "access": "write"},
                "roles": {"value": ["teacher"], "access": "write"},
            },
        }
    }


@pytest.mark.e2e
@pytest.mark.parametrize(
    "username, password", [("max.student", "univention"), ("mina.teacher", "univention")]
)
@pytest.mark.asyncio
async def test_create_user_not_allowed(access_token, base_url, get_kelvin_user, username, password):
    token = access_token(username, password)
    user = {
        "first_name": "Max",
        "last_name": "Mustermann",
        "username": "max.mustermann",
        "roles": ["teacher"],
        "school": "school1",
        "school_classes": [],
        "disabled": False,
        "password": "univention",
    }
    response = requests.post(
        f"{base_url}/bff/users", headers={"Authorization": f"Bearer {token}"}, json=user
    )
    assert response.status_code == 403, response.json()
    assert response.json()["detail"] == "You do not have the permission to create this user."
    assert set(response.json()["missingPermissions"]) == {
        "create-user",
        "write-first_name",
        "write-schools",
        "write-roles",
        "write-username",
        "write-disabled",
        "write-school_classes",
        "write-last_name",
        "write-password",
    }


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_create_user_not_allowed_wrong_school(access_token, base_url, get_kelvin_user):
    token = access_token("alex.admin", "univention")
    user = {
        "first_name": "Max",
        "last_name": "Mustermann",
        "username": "max.mustermann",
        "roles": ["teacher"],
        "school": "school2",
        "school_classes": [],
        "disabled": False,
        "password": "univention",
    }
    response = requests.post(
        f"{base_url}/bff/users", headers={"Authorization": f"Bearer {token}"}, json=user
    )
    assert response.status_code == 403, response.json()
    assert response.json()["detail"] == "You do not have the permission to create this user."
    assert set(response.json()["missingPermissions"]) == {
        "create-user",
        "write-first_name",
        "write-schools",
        "write-roles",
        "write-username",
        "write-disabled",
        "write-school_classes",
        "write-last_name",
        "write-password",
    }


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_delete_user(access_token, base_url, kelvin_user_factory):
    token = access_token("alex.admin", "univention")
    user = await kelvin_user_factory(school="school1", schools=["school1"], roles=["teacher"])

    def search_and_assert_existence(identifier: str, should_exist: bool):
        params = {"school": "school1"}
        response = requests.get(
            f"{base_url}/bff/users", headers={"Authorization": f"Bearer {token}"}, params=params
        )
        json = response.json()
        user_ids = set([user["id"] for user in json["users"]])
        if should_exist:
            assert identifier in user_ids
        else:
            assert identifier not in user_ids

    def delete_user_and_assert_204(identifier: str):
        response = requests.delete(
            f"{base_url}/bff/users/{identifier}", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 204

    user_to_delete = user.name
    search_and_assert_existence(user_to_delete, True)
    delete_user_and_assert_204(user_to_delete)
    search_and_assert_existence(user_to_delete, False)
    delete_user_and_assert_204(user_to_delete)


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_patch_user(access_token, base_url, kelvin_user_factory, get_kelvin_user):
    token = access_token("alex.admin", "univention")
    kelvin_user = await kelvin_user_factory(schools=["school1"], school="school1", roles=["teacher"])
    response = requests.patch(
        f"{base_url}/bff/users/{kelvin_user.name}",
        params={"school": "school1"},
        json={"first_name": "John"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.json()
    assert response.json()["user"]["attributes"]["first_name"]["value"] == "John"
    patched_kelvin_user = await get_kelvin_user(kelvin_user.name)
    kelvin_user.firstname = "John"
    assert patched_kelvin_user.as_dict() == kelvin_user.as_dict()


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_patch_user_not_allowed(access_token, base_url, kelvin_user_factory):
    token = access_token("mina.teacher", "univention")
    kelvin_user = await kelvin_user_factory(schools=["school1"], school="school1", roles=["teacher"])
    response = requests.patch(
        f"{base_url}/bff/users/{kelvin_user.name}",
        params={"school": "school1"},
        json={"last_name": "Meyer"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403, response.json()
    assert response.json()["detail"] == "You do not have the permission to edit this user."
    assert response.json()["missingPermissions"] == ["write-last_name"]


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_patch_user_wrong_school(access_token, base_url, kelvin_user_factory, get_kelvin_user):
    token = access_token("mina.teacher", "univention")
    kelvin_user = await kelvin_user_factory(schools=["school1"], school="school1", roles=["teacher"])
    response = requests.patch(
        f"{base_url}/bff/users/{kelvin_user.name}",
        params={"school": "school5"},
        json={"first_name": "John"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400, response.json()
    assert response.json() == {"detail": f"Cannot patch user '{kelvin_user.name}' in school 'school5'."}


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_patch_user_not_found(access_token, base_url, kelvin_user_factory, get_kelvin_user):
    token = access_token("mina.teacher", "univention")
    response = requests.patch(
        f"{base_url}/bff/users/NON_EXISTENT",
        params={"school": "school5"},
        json={"first_name": "John"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404, response.json()
    assert response.json() == {"detail": "Object not found: NON_EXISTENT"}


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_patch_user_multi_school(access_token, base_url, kelvin_user_factory, get_kelvin_user):
    token = access_token("alex.admin", "univention")
    kelvin_user = await kelvin_user_factory(
        schools=["school1", "school2"],
        school="school1",
        roles=["teacher"],
        school_classes={"school1": ["1a", "2a"], "school2": ["1b", "2b"]},
    )
    response = requests.patch(
        f"{base_url}/bff/users/{kelvin_user.name}",
        params={"school": "school1"},
        json={"school_classes": ["1c"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.json()
    assert response.json()["user"]["attributes"]["classes"]["value"] == [
        "school1:1c",
        "school2:1b",
        "school2:2b",
    ]
    patched_kelvin_user = await get_kelvin_user(kelvin_user.name)
    kelvin_user.school_classes["school1"] = ["1c"]
    assert patched_kelvin_user.as_dict() == kelvin_user.as_dict()


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_get_user_add_config(access_token, base_url, kelvin_school_class_factory):
    token = access_token("alex.admin", "univention")
    school_class = await kelvin_school_class_factory(school="school1", name="test_school_class_1")
    response = requests.get(
        f"{base_url}/bff/config/users/add",
        params={"school": "school1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.json()

    assert {
        "attributes": {"class_name": {"label": school_class.name, "value": school_class.name}},
        "id": school_class.name,
    } in next(
        filter(
            lambda x: x["props"]["name"] == "school_classes",
            response.json()["pages"][0]["fieldsets"][0]["rows"],
        )
    )[
        "props"
    ][
        "rows"
    ]
