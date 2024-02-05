# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import pytest


def test_get_users_config(test_client, api_prefix):
    response = test_client.get(f"{api_prefix}/config-users")
    assert response.status_code == 200, response.json()
    assert response.json() == {
        "columns": [
            {
                "label": "Last name",
                "attribute": "last_name",
                "formatter": "string",
                "sorting": "asc",
                "order": 0,
            },
            {
                "label": "First name",
                "attribute": "first_name",
                "formatter": "string",
                "sorting": "asc",
                "order": 1,
            },
            {
                "label": "Username",
                "attribute": "username",
                "formatter": "string",
                "sorting": "asc",
                "order": 2,
            },
            {
                "label": "Schools",
                "attribute": "schools",
                "formatter": "list",
                "sorting": "asc",
                "order": 3,
            },
            {
                "label": "Activation state",
                "attribute": "disabled",
                "formatter": "string",
                "sorting": "asc",
                "order": 4,
            },
            {
                "label": "Roles",
                "attribute": "ucsschool_roles",
                "formatter": "list",
                "sorting": "asc",
                "order": 5,
            },
        ]
    }


@pytest.mark.parametrize(
    "school,expected_users",
    [
        ("NON_EXISTENT", []),
        (
            "test_school1",
            [
                {
                    "attributes": {
                        "disabled": False,
                        "first_name": "firstname",
                        "last_name": "lastname",
                        "roles": ["teacher:school:test_school1"],
                        "schools": ["test_school1"],
                        "username": "firstname.lastname",
                    },
                    "id": "test_user1",
                }
            ],
        ),
        (
            "test_school2",
            [
                {
                    "attributes": {
                        "disabled": False,
                        "first_name": "firstname2",
                        "last_name": "lastname2",
                        "roles": ["teacher:school:test_school2"],
                        "schools": ["test_school2"],
                        "username": "firstname2.lastname2",
                    },
                    "id": "test_user2",
                },
                {
                    "attributes": {
                        "disabled": False,
                        "first_name": "firstname3",
                        "last_name": "lastname3",
                        "roles": [
                            "teacher:school:test_school2",
                            "student:school:test_school3",
                        ],
                        "schools": ["test_school2", "test_school3"],
                        "username": "firstname3.lastname3",
                    },
                    "id": "test_user3",
                },
            ],
        ),
    ],
)
def test_get_users(school, expected_users, test_client, api_prefix):
    response = test_client.get(f"{api_prefix}/users", params={"school": school})
    assert response.status_code == 200, response.json()
    assert response.json() == {
        "users": [
            {
                "id": user["id"],
                "attributes": {
                    name: {"value": value, "visible": True} for name, value in user["attributes"].items()
                },
            }
            for user in expected_users
        ]
    }


def test_get_schools(test_client, api_prefix):
    input_data = [
        {"display_name": "School 1", "id": "school1"},
        {"display_name": "School 2", "id": "school2"},
        {"display_name": "School 3", "id": "school3"},
    ]

    response = test_client.get(f"{api_prefix}/schools")
    assert response.status_code == 200, response.json()
    assert response.json() == {
        "schools": [
            {
                "value": school["id"],
                "label": school["display_name"],
            }
            for school in input_data
        ]
    }
