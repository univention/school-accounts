# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import json
import os
from unittest.mock import MagicMock, patch

import pytest

from user_management_bff.adapter_registry import port_dep
from user_management_bff.adapters.permissions import FilePermissionsAdapter
from user_management_bff.adapters.users import FileUsersPersistenceAdapter
from user_management_bff.errors import CreationError, ObjectNotFoundError
from user_management_bff.main import app
from user_management_bff.ports import PermissionsPort


def test_get_users_config(test_client, api_prefix):
    response = test_client.get(f"{api_prefix}/config/users/list")
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
    response = test_client.get(f"{api_prefix}/config/app")
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
                        "active": True,
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
                        "active": True,
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
                        "active": True,
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
                    name: {"value": value, "access": "write"}
                    for name, value in transform_user_dict_to_api_users_dict(user)["attributes"].items()
                },
            }
            for user in expected_users
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
@patch.object(FilePermissionsAdapter, "get_permissions", return_value={})
def test_get_users_no_permissions(
    _permissions_mock,
    school,
    expected_users,
    test_client,
    api_prefix,
    transform_user_dict_to_api_users_dict,
):
    response = test_client.get(f"{api_prefix}/users", params={"school": school})
    assert response.status_code == 200, response.json()
    assert response.json() == {
        "users": [
            {
                "id": user["id"],
                "allowedActions": [],
                "attributes": {
                    name: (
                        {"value": value, "access": "read"}
                        if name == "username"
                        else {"value": None, "access": "none"}
                    )
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

    response = test_client.get(f"{api_prefix}/config/schools")
    assert response.status_code == 200, response.json()
    assert response.json() == {
        "schools": [
            {"value": school["id"], "label": school["display_name"], "permissions": ["add"]}
            for school in input_data
        ]
    }


@pytest.mark.usefixtures("restore_users_json")
def test_create_user(test_client, api_prefix, transform_user_dict_to_api_users_dict):
    user = {
        "first_name": "firstname",
        "last_name": "lastname",
        "username": "username",
        "roles": [
            "teacher",
        ],
        "school": "test_school1",
        "school_classes": ["1a", "2b"],
        "disabled": False,
        "password": "password",
    }
    response = test_client.post(f"{api_prefix}/users", json=user)
    assert response.status_code == 201, response.json()
    expected_user = {
        "id": user["username"],
        "attributes": {
            "first_name": {"value": user["first_name"], "access": "write"},
            "last_name": {"value": user["last_name"], "access": "write"},
            "username": {"value": user["username"], "access": "write"},
            "schools": {"value": [user["school"]], "access": "write"},
            "classes": {"value": ["test_school1:1a", "test_school1:2b"], "access": "write"},
            "activated": {"value": not user["disabled"], "access": "write"},
            "roles": {"value": user["roles"], "access": "write"},
        },
    }
    assert response.json() == {"user": expected_user}
    # check that the user was created in the persistence adapter
    with open(os.environ["FILE_USERS_PERSISTENCE_ADAPTER__SOURCE"], "r") as file:
        users = json.load(file)

    assert users[-1]["id"] == user["username"]


@patch("user_management_bff.business_logic.create_user", side_effect=CreationError("error"))
def test_create_user_creation_error(mock_save, test_client, api_prefix):
    user = {
        "first_name": "firstname",
        "last_name": "lastname",
        "username": "username",
        "roles": [
            "teacher",
        ],
        "school": "test_school1",
        "school_classes": ["1a", "2b"],
        "disabled": False,
        "password": "password",
    }
    mock_permssions_port = MagicMock()
    app.dependency_overrides[port_dep(PermissionsPort)] = lambda: mock_permssions_port
    response = test_client.post(f"{api_prefix}/users", json=user)
    mock_save.called_once()
    assert response.status_code == 400, response.json()
    assert response.json() == {"detail": "error"}


@patch.object(FilePermissionsAdapter, "get_permissions", return_value={})
def test_create_user_permissions_error(
    mock_create_user, test_client, api_prefix, transform_user_dict_to_api_users_dict
):
    user = {
        "first_name": "firstname",
        "last_name": "lastname",
        "username": "bad_username",
        "roles": [
            "teacher",
        ],
        "school": "test_school1",
        "school_classes": ["1a", "2b"],
        "disabled": False,
        "password": "password",
    }
    response = test_client.post(f"{api_prefix}/users", json=user)
    assert response.status_code == 403, response.json()

    mock_create_user.called_once()

    # check that the user was not created in the persistence adapter
    with open(os.environ["FILE_USERS_PERSISTENCE_ADAPTER__SOURCE"], "r") as file:
        users = json.load(file)

    assert users[-1]["id"] != user["username"]


def test_delete_user_non_existent(test_client, api_prefix):
    identifier = "NON_EXISTENT"  # depends on this id not being in dev/data/users.json
    response = test_client.delete(f"{api_prefix}/users/{identifier}")
    assert response.status_code == 204


@pytest.mark.usefixtures("restore_users_json")
def test_delete_user(test_client, api_prefix):
    identifier = "test_user1"
    response = test_client.delete(f"{api_prefix}/users/{identifier}")
    assert response.status_code == 204


@patch.object(FilePermissionsAdapter, "get_permissions", return_value={})
def test_delete_user_not_allowed(_permission_mock, test_client, api_prefix):
    identifier = "test_user1"
    response = test_client.delete(f"{api_prefix}/users/{identifier}")
    assert response.status_code == 403


@patch.object(FileUsersPersistenceAdapter, "delete_user", side_effect=ObjectNotFoundError("ID"))
def test_delete_user_race_condition(_delete_mock, test_client, api_prefix):
    identifier = "test_user1"
    response = test_client.delete(f"{api_prefix}/users/{identifier}")
    assert response.status_code == 204


@pytest.mark.usefixtures("restore_users_json")
def test_patch_user_wrong_school(test_client, api_prefix):
    response = test_client.patch(
        f"{api_prefix}/users/test_user1", params={"school": "NON_EXISTENT"}, json={}
    )
    assert response.status_code == 400, response.json()
    assert response.json() == {"detail": "Cannot patch user 'test_user1' in school 'NON_EXISTENT'."}


@pytest.mark.usefixtures("restore_users_json")
def test_patch_user_not_found(test_client, api_prefix):
    response = test_client.patch(
        f"{api_prefix}/users/NON_EXISTENT", params={"school": "NON_EXISTENT"}, json={}
    )
    assert response.status_code == 404, response.json()
    assert response.json() == {"detail": "Object not found: NON_EXISTENT"}


@patch.object(FilePermissionsAdapter, "get_permissions", return_value={})
def test_patch_user_not_allowed(_mock_permission_adapter, test_client, api_prefix):
    response = test_client.patch(
        f"{api_prefix}/users/test_user1", params={"school": "test_school1"}, json={"first_name": "John"}
    )
    print(response)
    assert response.status_code == 403, response.json()
    assert response.json()["detail"] == "You do not have the permission to edit this user."
    assert response.json()["missingPermissions"] == ["write-first_name"]


@pytest.mark.parametrize(
    "patch_dict", [{}, {"first_name": "John"}, {"first_name": "John", "username": "jon.doe"}]
)
@pytest.mark.usefixtures("restore_users_json")
def test_patch_user(test_client, api_prefix, patch_dict, users_json_path):
    response = test_client.patch(
        f"{api_prefix}/users/test_user1", params={"school": "test_school1"}, json=patch_dict
    )
    original_user = {
        "attributes": {
            "activated": {"access": "write", "value": True},
            "classes": {"access": "write", "value": ["test_school1:1a", "test_school1:2b"]},
            "first_name": {"access": "write", "value": "firstname"},
            "last_name": {"access": "write", "value": "lastname"},
            "roles": {"access": "write", "value": ["teacher:school:test_school1"]},
            "schools": {"access": "write", "value": ["test_school1"]},
            "username": {"access": "write", "value": "firstname.lastname"},
        },
        "id": "test_user1",
    }
    for key, value in patch_dict.items():
        original_user["attributes"][key]["value"] = value
    assert response.status_code == 200, response.json()
    assert response.json()["user"] == original_user


@pytest.mark.usefixtures("restore_users_json")
def test_patch_user_school_classes(test_client, api_prefix):
    response = test_client.patch(
        f"{api_prefix}/users/test_user3",
        params={"school": "test_school2"},
        json={"school_classes": ["1a"]},
    )
    assert response.status_code == 200
    assert response.json()["user"]["attributes"]["classes"]["value"] == [
        "test_school1:1a",
        "test_school1:2b",
        "test_school2:1a",
    ]


def test_get_user_add_config(test_client, api_prefix):
    response = test_client.get(f"{api_prefix}/config/users/add?school=school1")
    assert response.status_code == 200, response.json()
    assert response.json() == {
        "pages": [
            {
                "fieldsets": [
                    {
                        "label": "User Info",
                        "name": "userinfo",
                        "rows": [
                            {
                                "props": {
                                    "access": "read",
                                    "description": "School of the user",
                                    "label": "School",
                                    "name": "school",
                                    "required": True,
                                    "options": [
                                        {"label": "School1", "value": "school1"},
                                    ],
                                },
                                "type": "UComboBox",
                                "watches": [],
                            },
                            [
                                {
                                    "props": {
                                        "access": "write",
                                        "description": "Last name of the user",
                                        "label": "Last name",
                                        "name": "last_name",
                                        "required": True,
                                    },
                                    "type": "UInputText",
                                    "watches": [],
                                },
                                {
                                    "props": {
                                        "access": "write",
                                        "description": "First name of the user",
                                        "label": "First name",
                                        "name": "first_name",
                                        "required": True,
                                    },
                                    "type": "UInputText",
                                    "watches": [],
                                },
                            ],
                            {
                                "props": {
                                    "access": "write",
                                    "description": "Username of the user",
                                    "label": "Username",
                                    "name": "username",
                                    "required": True,
                                },
                                "type": "UInputText",
                                "watches": [],
                            },
                            {
                                "props": {
                                    "access": "write",
                                    "description": "Password of the user",
                                    "label": "Password",
                                    "name": "password",
                                    "required": False,
                                },
                                "type": "UInputPassword",
                                "watches": [],
                            },
                            {
                                "props": {
                                    "access": "write",
                                    "columns": [
                                        {
                                            "attribute": "class_name",
                                            "formatter": None,
                                            "label": "School class",
                                            "order": 0,
                                            "sorting": None,
                                        }
                                    ],
                                    "description": "School classes of the user",
                                    "label": "School classes",
                                    "name": "school_classes",
                                    "required": True,
                                    "rows": [
                                        {
                                            "attributes": {
                                                "class_name": {"access": "read", "value": "1a"}
                                            },
                                            "id": "1a",
                                        },
                                        {
                                            "attributes": {
                                                "class_name": {"access": "read", "value": "2b"}
                                            },
                                            "id": "2b",
                                        },
                                    ],
                                },
                                "type": "UMultiSelect",
                                "watches": [],
                            },
                            {
                                "props": {
                                    "access": "write",
                                    "description": "Roles of the user",
                                    "label": "Roles",
                                    "name": "roles",
                                    "required": True,
                                    "columns": [
                                        {
                                            "label": "Role",
                                            "attribute": "role_name",
                                            "sorting": None,
                                            "order": 0,
                                            "formatter": None,
                                        },
                                    ],
                                    "rows": [
                                        {
                                            "id": "student",
                                            "attributes": {
                                                "role_name": {
                                                    "value": "Student",
                                                    "access": "read",
                                                },
                                            },
                                        },
                                        {
                                            "id": "teacher",
                                            "attributes": {
                                                "role_name": {
                                                    "value": "Teacher",
                                                    "access": "read",
                                                },
                                            },
                                        },
                                    ],
                                },
                                "type": "UMultiSelect",
                                "watches": [],
                            },
                            {
                                "props": {
                                    "access": "write",
                                    "description": "Active",
                                    "label": "Active",
                                    "name": "active",
                                    "required": False,
                                },
                                "type": "UInputCheckbox",
                                "watches": [],
                            },
                        ],
                    }
                ],
                "label": "Add user",
                "name": "useradd",
            }
        ]
    }
