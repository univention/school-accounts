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
        "schools": ["school1"],
        "school_classes": {},
        "disabled": False,
    }
    response = requests.post(
        f"{base_url}/bff/user", headers={"Authorization": f"Bearer {token}"}, json=user
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
