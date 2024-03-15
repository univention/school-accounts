# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import pytest
import requests


@pytest.mark.e2e
def test_create_user(access_token, base_url, kelvin_user_deletion):
    token = access_token("mina.teacher", "univention")
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
                "last_name": {"value": "Mustermann", "access": "read"},
                "first_name": {"value": "Max", "access": "read"},
                "username": {"value": "max.mustermann", "access": "read"},
                "activated": {"value": True, "access": "read"},
                "schools": {"value": ["school1"], "access": "read"},
                "classes": {"value": [], "access": "read"},
                "roles": {"value": ["teacher"], "access": "read"},
            },
        }
    }


@pytest.mark.e2e
def test_delete_user(access_token, base_url):
    token = access_token("mina.teacher", "univention")

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

    user_to_delete = "to.delete"
    search_and_assert_existence(user_to_delete, True)
    delete_user_and_assert_204(user_to_delete)
    search_and_assert_existence(user_to_delete, False)
    delete_user_and_assert_204(user_to_delete)


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_patch_user(access_token, base_url, kelvin_user_factory, get_kelvin_user):
    token = access_token("mina.teacher", "univention")
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
    assert response.json() == {"detail": "Cannot patch user 'Megan.Chang' in school 'school5'."}


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
    token = access_token("mina.teacher", "univention")
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
