# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import json
import os
from unittest.mock import patch

import pytest

from user_management_bff.errors import CreationError


def test_get_users_config(test_client, api_prefix):
    response = test_client.get(f"{api_prefix}/config-users")
    assert response.status_code == 200, response.json()
    assert response.json() == {
        "columns": [
            {
                "label": "Last name",
                "attribute": "last_name",
                "formatter": None,
                "sorting": "asc",
                "order": 0,
            },
            {
                "label": "First name",
                "attribute": "first_name",
                "formatter": None,
                "sorting": "asc",
                "order": 1,
            },
            {
                "label": "Username",
                "attribute": "username",
                "formatter": None,
                "sorting": None,
                "order": 2,
            },
            {
                "label": "Roles",
                "attribute": "roles",
                "formatter": {"type": "list"},
                "sorting": None,
                "order": 3,
            },
            {
                "label": "Classes",
                "attribute": "classes",
                "formatter": {"type": "list"},
                "sorting": None,
                "order": 4,
            },
            {
                "label": "Schools",
                "attribute": "schools",
                "formatter": {"type": "list"},
                "sorting": None,
                "order": 5,
            },
            {
                "label": "Activated",
                "attribute": "activated",
                "formatter": {"type": "boolean"},
                "sorting": None,
                "order": 6,
            },
        ]
    }


@pytest.mark.parametrize(
    "environ,expected_response",
    [
        (
            {
                "COLORTERM": "truecolor",
                "SHELL": "/bin/bash",
                "SUPER_SECRET_PASSWORD": "password1234",
            },
            {},
        ),
        (
            {
                "LOGNAME": "admin",
                "VITE__VALUE_1": "foo",
                "VITE__VALUE_2__SUBVALUE_1": "bar1",
                "VITE__VALUE_2__SUBVALUE_2": "bar2",
                "YOLO": "1",
            },
            {
                "VITE__VALUE_1": "foo",
                "VITE__VALUE_2__SUBVALUE_1": "bar1",
                "VITE__VALUE_2__SUBVALUE_2": "bar2",
            },
        ),
    ],
)
def test_get_app_config(
    test_client, api_prefix, patch_test_env, environ, expected_response, monkeypatch
):
    for key in os.environ.keys():
        if key.startswith("VITE__"):
            monkeypatch.delenv(key)
    patch_test_env(environ)
    response = test_client.get(f"{api_prefix}/config-app")
    assert response.status_code == 200, response.json()
    assert response.json() == expected_response


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
                        "school_classes": {"test_school1": ["1a", "2b"]},
                        "username": "firstname.lastname",
                    },
                    "allowedActions": ["delete"],
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
                        "school_classes": {"test_school2": ["1a", "2b"]},
                        "username": "firstname2.lastname2",
                    },
                    "allowedActions": ["delete"],
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
                        "school_classes": {"test_school1": ["1a", "2b"], "test_school2": ["3c"]},
                        "username": "firstname3.lastname3",
                    },
                    "allowedActions": ["delete"],
                    "id": "test_user3",
                },
            ],
        ),
    ],
)
def test_get_users(
    school, expected_users, test_client, api_prefix, transform_user_dict_to_api_users_dict
):
    response = test_client.get(f"{api_prefix}/users", params={"school": school})
    assert response.status_code == 200, response.json()
    assert response.json() == {
        "users": [
            {
                "id": user["id"],
                "allowedActions": ["delete"],
                "attributes": {
                    name: {"value": value, "access": "read"}
                    for name, value in transform_user_dict_to_api_users_dict(user)["attributes"].items()
                },
            }
            for user in expected_users
        ]
    }


def test_config_schools(test_client, api_prefix):
    input_data = [
        {"display_name": "School 1", "id": "school1"},
        {"display_name": "School 2", "id": "school2"},
        {"display_name": "School 3", "id": "school3"},
    ]

    response = test_client.get(f"{api_prefix}/config-schools")
    assert response.status_code == 200, response.json()
    assert response.json() == {
        "schools": [
            {"value": school["id"], "label": school["display_name"], "permissions": ["add"]}
            for school in input_data
        ]
    }


def test_create_user(test_client, api_prefix, transform_user_dict_to_api_users_dict):
    # backup json file
    with open(os.environ["FILE_USERS_PERSISTENCE_ADAPTER__SOURCE"], "r") as file:
        data = file.read()

    user = {
        "first_name": "firstname",
        "last_name": "lastname",
        "username": "username",
        "roles": [
            "teacher",
        ],
        "schools": ["test_school1"],
        "school_classes": {"test_school1": ["1a", "2b"]},
        "disabled": False,
        "password": "password",
    }
    response = test_client.post(f"{api_prefix}/users", json=user)
    assert response.status_code == 201, response.json()
    expected_user = {
        "id": user["username"],
        "attributes": {
            "first_name": {"value": user["first_name"], "access": "read"},
            "last_name": {"value": user["last_name"], "access": "read"},
            "username": {"value": user["username"], "access": "read"},
            "schools": {"value": user["schools"], "access": "read"},
            "classes": {"value": ["test_school1:1a", "test_school1:2b"], "access": "read"},
            "activated": {"value": not user["disabled"], "access": "read"},
            "roles": {"value": user["roles"], "access": "read"},
        },
    }
    assert response.json() == {"user": expected_user}
    # check that the user was created in the persistence adapter
    with open(os.environ["FILE_USERS_PERSISTENCE_ADAPTER__SOURCE"], "r") as file:
        users = json.load(file)

    assert users[-1]["id"] == user["username"]

    # restore json file
    with open(os.environ["FILE_USERS_PERSISTENCE_ADAPTER__SOURCE"], "w") as file:
        file.write(data)


@patch("user_management_bff.business_logic.create_user", side_effect=CreationError("error"))
def test_create_user_error(mock_save, test_client, api_prefix):
    user = {
        "first_name": "firstname",
        "last_name": "lastname",
        "username": "username",
        "roles": [
            "teacher",
        ],
        "schools": ["test_school1"],
        "school_classes": {"test_school1": ["1a", "2b"]},
        "disabled": False,
        "password": "password",
    }
    response = test_client.post(f"{api_prefix}/users", json=user)
    mock_save.called_once()
    assert response.status_code == 400, response.json()
    assert response.json() == {"detail": "error"}


def test_delete_user_non_existent(test_client, api_prefix):
    # The tests are currently set up globally to use the FileUsersPersistenceAdapter
    # with dev/data/users.json as data.
    # For now we only test here that deleting a non existing user returns 204
    identifier = "NON_EXISTENT"  # depends on this id not being in dev/data/users.json
    response = test_client.delete(f"{api_prefix}/users/{identifier}")
    assert response.status_code == 204
