# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import pytest
import requests


@pytest.mark.e2e
def test_create_user(access_token, base_url):
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
    # TODO: remove created user from Kelvin


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
