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
from user_management_bff.errors import CreationError, NotAuthenticatedError, ObjectNotFoundError
from user_management_bff.lang import _
from user_management_bff.main import StaticFilesSPA, app
from user_management_bff.ports import PermissionsPort


@pytest.mark.parametrize("lang", ["en", "de"])
def test_get_users_config(test_client, api_prefix, lang):
    response = test_client.get(
        f"{api_prefix}/config/users/list",
        headers={"Accept-Language": lang},
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {
        "columns": [
            {
                "label": _("Last name", lang=lang),
                "attribute": "last_name",
                "formatter": None,
                "sorting": "asc",
                "order": 0,
            },
            {
                "label": _("First name", lang=lang),
                "attribute": "first_name",
                "formatter": None,
                "sorting": "asc",
                "order": 1,
            },
            {
                "label": _("Username", lang=lang),
                "attribute": "username",
                "formatter": None,
                "sorting": None,
                "order": 2,
            },
            {
                "label": _("Roles", lang=lang),
                "attribute": "roles",
                "formatter": {"type": "list"},
                "sorting": None,
                "order": 3,
            },
            {
                "label": _("Classes", lang=lang),
                "attribute": "classes",
                "formatter": {"type": "list"},
                "sorting": None,
                "order": 4,
            },
            {
                "label": _("Schools", lang=lang),
                "attribute": "schools",
                "formatter": {"type": "list"},
                "sorting": None,
                "order": 5,
            },
            {
                "label": _("Activated", lang=lang),
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
                        "activated": True,
                        "first_name": "firstname",
                        "last_name": "lastname",
                        "roles": ["teacher:school:test_school1"],
                        "schools": ["test_school1"],
                        "school_classes": {"test_school1": ["1a", "2b"]},
                        "username": "firstname.lastname",
                    },
                    "allowedActions": ["delete"],
                    "id": "test_user1",
                },
                {
                    "attributes": {
                        "activated": True,
                        "first_name": "firstname4",
                        "last_name": "lastname4",
                        "roles": ["school_admin:school:test_school1"],
                        "school_classes": {"test_school1": ["1a"]},
                        "schools": ["test_school1"],
                        "username": "firstname4.lastname4",
                    },
                    "allowedActions": ["delete"],
                    "id": "test_user4",
                },
            ],
        ),
        (
            "test_school2",
            [
                {
                    "attributes": {
                        "activated": True,
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
                        "activated": True,
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
                        "activated": True,
                        "first_name": "firstname",
                        "last_name": "lastname",
                        "roles": ["teacher:school:test_school1"],
                        "schools": ["test_school1"],
                        "school_classes": {"test_school1": ["1a", "2b"]},
                        "username": "firstname.lastname",
                    },
                    "allowedActions": ["delete"],
                    "id": "test_user1",
                },
                {
                    "attributes": {
                        "activated": True,
                        "first_name": "firstname4",
                        "last_name": "lastname4",
                        "roles": ["school_admin:school:test_school1"],
                        "school_classes": {"test_school1": ["1a"]},
                        "schools": ["test_school1"],
                        "username": "firstname4.lastname4",
                    },
                    "allowedActions": ["delete"],
                    "id": "test_user4",
                },
            ],
        ),
        (
            "test_school2",
            [
                {
                    "attributes": {
                        "activated": True,
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
                        "activated": True,
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
        {"display_name": "Test School 1", "id": "test_school1"},
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
            "roles": {
                "value": [f"{role}:school:{user['school']}" for role in user["roles"]],
                "access": "write",
            },
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
@pytest.mark.parametrize("lang", ["en", "de"])
def test_create_user_permissions_error(
    mock_create_user, test_client, api_prefix, transform_user_dict_to_api_users_dict, lang
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
    response = test_client.post(
        f"{api_prefix}/users",
        json=user,
        headers={"Accept-Language": lang},
    )
    response_json = response.json()
    assert response.status_code == 403, response_json
    assert response_json["detail"] == _(
        "You do not have the permission to create this user.", lang=lang
    ), response_json

    mock_create_user.called_once()

    # check that the user was not created in the persistence adapter
    with open(os.environ["FILE_USERS_PERSISTENCE_ADAPTER__SOURCE"], "r") as file:
        users = json.load(file)

    assert users[-1]["id"] != user["username"]


@pytest.mark.parametrize("lang", ["en", "de"])
def test_create_user_classes_validation_error(test_client, api_prefix, lang):
    user = {
        "first_name": "firstname",
        "last_name": "lastname",
        "username": "bad_username",
        "roles": [
            "student",
        ],
        "school": "test_school1",
        "school_classes": [],
        "disabled": False,
        "password": "password",
    }
    response = test_client.post(
        f"{api_prefix}/users",
        json=user,
        headers={"Accept-Language": lang},
    )
    response_json = response.json()
    response_detail = response_json["detail"]
    assert response.status_code == 422, response_json
    assert len(response_detail) == 1, response_json
    assert response_detail[0]["loc"] == [_("general", lang=lang)]
    assert response_detail[0]["msg"] == _(
        "A student must be member of at least one school class.", lang=lang
    )


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
@pytest.mark.parametrize("lang", ["en", "de"])
def test_delete_user_not_allowed(_permission_mock, test_client, api_prefix, lang):
    identifier = "test_user1"
    response = test_client.delete(
        f"{api_prefix}/users/{identifier}",
        headers={"Accept-Language": lang},
    )
    response_json = response.json()
    assert response.status_code == 403, response_json
    assert response_json["detail"] == _("You do not have the permission to edit this user.", lang=lang)


@patch.object(FileUsersPersistenceAdapter, "delete_user", side_effect=ObjectNotFoundError("ID"))
def test_delete_user_race_condition(_delete_mock, test_client, api_prefix):
    identifier = "test_user1"
    response = test_client.delete(f"{api_prefix}/users/{identifier}")
    assert response.status_code == 204


@patch.object(
    FileUsersPersistenceAdapter,
    "delete_user",
    side_effect=NotAuthenticatedError(message="Not authenticated"),
)
def test_delete_user_not_authenticated(_delete_mock, test_client, api_prefix):
    identifier = "test_user1"
    response = test_client.delete(f"{api_prefix}/users/{identifier}")
    assert response.status_code == 401


@pytest.mark.usefixtures("restore_users_json")
@pytest.mark.parametrize("lang", ["en", "de"])
def test_patch_user_wrong_school(test_client, api_prefix, lang):
    user = "test_user1"
    school = "NON_EXISTENT"
    response = test_client.patch(
        f"{api_prefix}/users/{user}",
        params={"school": school},
        json={},
        headers={"Accept-Language": lang},
    )
    assert response.status_code == 400, response.json()
    assert response.json() == {
        "detail": _(f"Cannot update user '{user}' in school '{school}'.", lang=lang)
    }


@pytest.mark.usefixtures("restore_users_json")
@pytest.mark.parametrize("lang", ["en", "de"])
def test_patch_user_not_found(test_client, api_prefix, lang):
    response = test_client.patch(
        f"{api_prefix}/users/NON_EXISTENT",
        params={"school": "school1"},
        json={},
        headers={"Accept-Language": lang},
    )
    response_json = response.json()
    assert response.status_code == 404, response_json
    assert response_json == {"detail": f"{_('Object not found', lang=lang)}: NON_EXISTENT"}


@patch.object(FilePermissionsAdapter, "get_permissions", return_value={})
@pytest.mark.parametrize("lang", ["en", "de"])
def test_patch_user_not_allowed(_mock_permission_adapter, test_client, api_prefix, lang):
    response = test_client.patch(
        f"{api_prefix}/users/test_user1",
        params={"school": "test_school1"},
        json={"first_name": "John"},
        headers={"Accept-Language": lang},
    )
    response_json = response.json()
    assert response.status_code == 403, response_json
    assert response_json["detail"] == _("You do not have the permission to edit this user.", lang=lang)
    assert response_json["missingPermissions"] == ["write-first_name"]


@pytest.mark.parametrize(
    "patch_dict",
    [{}, {"first_name": "John"}, {"first_name": "John", "username": "jon.doe"}, {"activated": False}],
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


@pytest.mark.parametrize(
    "patch_dict",
    [{}, {"activated": False}],
)
@pytest.mark.usefixtures("restore_users_json")
def test_patch_user_activated(test_client, api_prefix, patch_dict, users_json_path):
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


@pytest.mark.parametrize("lang", ["en", "de"])
def test_get_user_add_config(test_client, api_prefix, lang):
    response = test_client.get(
        f"{api_prefix}/config/users/add?school=school1",
        headers={"Accept-Language": lang},
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {
        "pages": [
            {
                "fieldsets": [
                    {
                        "label": _("User info", lang=lang),
                        "name": "userinfo",
                        "rows": [
                            {
                                "props": {
                                    "access": "read",
                                    "description": _("School of the user", lang=lang),
                                    "label": _("School", lang=lang),
                                    "name": "school",
                                    "required": True,
                                    "options": [
                                        {"label": "School 1", "value": "school1"},
                                    ],
                                },
                                "type": "UComboBox",
                                "watches": [],
                            },
                            [
                                {
                                    "props": {
                                        "access": "write",
                                        "description": _("Last name of the user", lang=lang),
                                        "label": _("Last name", lang=lang),
                                        "name": "last_name",
                                        "required": True,
                                    },
                                    "type": "UInputText",
                                    "watches": [],
                                },
                                {
                                    "props": {
                                        "access": "write",
                                        "description": _("First name of the user", lang=lang),
                                        "label": _("First name", lang=lang),
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
                                    "description": _("Username of the user", lang=lang),
                                    "label": _("Username", lang=lang),
                                    "name": "username",
                                    "required": True,
                                },
                                "type": "UInputText",
                                "watches": [],
                            },
                            {
                                "props": {
                                    "access": "write",
                                    "description": _("Password of the user", lang=lang),
                                    "label": _("Password", lang=lang),
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
                                            "label": _("School class", lang=lang),
                                            "order": 0,
                                            "sorting": None,
                                        }
                                    ],
                                    "description": _("School classes of the user", lang=lang),
                                    "label": _("School classes", lang=lang),
                                    "name": "school_classes",
                                    "required": False,
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
                                    "description": _("Roles of the user", lang=lang),
                                    "label": _("Roles", lang=lang),
                                    "name": "roles",
                                    "required": True,
                                    "columns": [
                                        {
                                            "label": _("Role", lang=lang),
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
                                                    "value": _("Student", lang=lang),
                                                    "access": "read",
                                                },
                                            },
                                        },
                                        {
                                            "id": "teacher",
                                            "attributes": {
                                                "role_name": {
                                                    "value": _("Teacher", lang=lang),
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
                                    "description": _("User is activated", lang=lang),
                                    "label": _("Activated", lang=lang),
                                    "name": "activated",
                                    "required": False,
                                },
                                "type": "UInputCheckbox",
                                "watches": [],
                            },
                        ],
                    }
                ],
                "label": _("Add user", lang=lang),
                "name": "useradd",
            }
        ]
    }


@pytest.mark.parametrize("lang", ["en", "de"])
def test_get_user_add_config_school_doesnt_exist(test_client, api_prefix, lang):
    fake_school = "fake_school"
    response = test_client.get(
        f"{api_prefix}/config/users/add?school={fake_school}",
        headers={"Accept-Language": lang},
    )
    response_json = response.json()
    assert response.status_code == 404, response_json
    assert response_json == {"detail": f"{_('Object not found', lang=lang)}: {fake_school}"}


@pytest.mark.parametrize("lang", ["en", "de"])
def test_get_user_edit_config(test_client, api_prefix, lang):
    response = test_client.get(
        f"{api_prefix}/config/users/edit?school=school1&id=user3",
        headers={"Accept-Language": lang},
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {
        "id": "user3",
        "pages": [
            {
                "fieldsets": [
                    {
                        "label": _("User info", lang=lang),
                        "name": "userinfo",
                        "rows": [
                            {
                                "props": {
                                    "access": "read",
                                    "description": _("School of the user", lang=lang),
                                    "label": _("School", lang=lang),
                                    "name": "school",
                                    "options": [{"label": "School 1", "value": "school1"}],
                                    "required": True,
                                },
                                "type": "UComboBox",
                                "watches": [],
                            },
                            [
                                {
                                    "props": {
                                        "access": "write",
                                        "description": _("Last name of the user", lang=lang),
                                        "label": _("Last name", lang=lang),
                                        "name": "last_name",
                                        "required": True,
                                    },
                                    "type": "UInputText",
                                    "watches": [],
                                },
                                {
                                    "props": {
                                        "access": "write",
                                        "description": _("First name of the user", lang=lang),
                                        "label": _("First name", lang=lang),
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
                                    "description": _("Username of the user", lang=lang),
                                    "label": _("Username", lang=lang),
                                    "name": "username",
                                    "required": False,
                                },
                                "type": "UInputText",
                                "watches": [],
                            },
                            {
                                "props": {
                                    "access": "write",
                                    "description": _("Password of the user", lang=lang),
                                    "label": _("Password", lang=lang),
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
                                            "label": _("School class", lang=lang),
                                            "order": 0,
                                            "sorting": None,
                                        }
                                    ],
                                    "description": _("School classes of the user", lang=lang),
                                    "label": _("School classes", lang=lang),
                                    "name": "school_classes",
                                    "required": False,
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
                                    "columns": [
                                        {
                                            "attribute": "role_name",
                                            "formatter": None,
                                            "label": _("Role", lang=lang),
                                            "order": 0,
                                            "sorting": None,
                                        }
                                    ],
                                    "description": _("Roles of the user", lang=lang),
                                    "label": _("Roles", lang=lang),
                                    "name": "roles",
                                    "required": True,
                                    "rows": [
                                        {
                                            "attributes": {
                                                "role_name": {
                                                    "access": "read",
                                                    "value": _("Student", lang=lang),
                                                }
                                            },
                                            "id": "student",
                                        },
                                        {
                                            "attributes": {
                                                "role_name": {
                                                    "access": "read",
                                                    "value": _("Teacher", lang=lang),
                                                }
                                            },
                                            "id": "teacher",
                                        },
                                        {
                                            "attributes": {
                                                "role_name": {
                                                    "access": "read",
                                                    "value": _("Staff", lang=lang),
                                                }
                                            },
                                            "id": "staff",
                                        },
                                        {
                                            "attributes": {
                                                "role_name": {
                                                    "access": "read",
                                                    "value": _("Administrator", lang=lang),
                                                }
                                            },
                                            "id": "administrator",
                                        },
                                    ],
                                },
                                "type": "UMultiSelect",
                                "watches": [],
                            },
                            {
                                "props": {
                                    "access": "write",
                                    "description": _("User is activated", lang=lang),
                                    "label": _("Activated", lang=lang),
                                    "name": "activated",
                                    "required": False,
                                },
                                "type": "UInputCheckbox",
                                "watches": [],
                            },
                        ],
                    }
                ],
                "label": _("User detail", lang=lang),
                "name": "useredit",
            }
        ],
        "user": {
            "activated": True,
            "first_name": "Kim",
            "last_name": "Klein",
            "password": None,
            "roles": ["teacher"],
            "school": "school1",
            "school_classes": ["1a", "2b"],
            "username": "kim.klein",
        },
    }


def test_get_user_edit_config_non_existing_user(test_client, api_prefix):
    response = test_client.get(f"{api_prefix}/config/users/edit?school=test_school1&id=NON_EXISTING")
    assert response.status_code == 404, response.json()
    assert response.json() == {"detail": "The user was not found in the school."}


def test_get_user_edit_config_wrong_school(test_client, api_prefix):
    response = test_client.get(f"{api_prefix}/config/users/edit?school=school1&id=test_user1")
    assert response.status_code == 404, response.json()
    assert response.json() == {"detail": "The user was not found in the school."}


@pytest.mark.parametrize("lang", ["en", "de"])
def test_get_user_edit_config_school_doesnt_exist(test_client, api_prefix, lang):
    fake_school = "fake_school"
    response = test_client.get(
        f"{api_prefix}/config/users/edit?school={fake_school}&id=test_user1",
        headers={"Accept-Language": lang},
    )
    response_json = response.json()
    assert response.status_code == 404, response_json
    assert response_json == {"detail": _("The user was not found in the school.", lang=lang)}


@pytest.mark.parametrize(
    "patch_dict",
    [
        {
            "roles": [
                "student",
            ]
        },
        {
            "roles": [
                "student",
                "teacher",
            ]
        },
        {
            "roles": [
                "student",
                "teacher",
                "administrator",
                "staff",
            ]
        },
        {
            "roles": [
                "teacher",
            ]
        },
    ],
)
def test_patch_user_change_roles(test_client, api_prefix, patch_dict):
    response = test_client.patch(f"{api_prefix}/users/{'dev'}?school={'school1'}", json=patch_dict)
    assert response.status_code == 200, response.json()
    roles = response.json()["user"]["attributes"]["roles"]["value"]
    # We currently block the roles from being updated
    expected_roles = ["teacher:school:school1"]
    assert roles == expected_roles


def test_admin_backend_to_frontend_conversion(test_client, api_prefix):
    response = test_client.get(f"{api_prefix}/config/users/edit?id=test_user4&school=test_school1")
    assert response.status_code == 200, response.json()
    assert response.json()["user"]["roles"] == ["administrator"]


@pytest.mark.asyncio
async def test_StaticFilesSPA_get_response(tmp_path, test_client):
    test_index = tmp_path / "index.html"
    test_index.write_text("index")
    test_page = tmp_path / "page.html"
    test_page.write_text("page")
    app.mount("/static_test", StaticFilesSPA(directory=tmp_path, html=True), name="static_test")
    resp = test_client.get("/static_test/foo.html")
    assert resp.text == "index"
    resp = test_client.get("/static_test/page.html")
    assert resp.text == "page"
