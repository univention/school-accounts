#!/usr/bin/env python3.7
# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Script to create the necessary Guardian objects fot the User management App."""
import base64
import json
from pathlib import Path

import requests
import sys
from functools import lru_cache

if len(sys.argv) != 7:
    print(
        f"Usage: {sys.argv[0]} <management_url> <username> <password> <keycloak_url> <keycloak_client> <condition_dir>"
    )
    sys.exit(1)

GUARDIAN_MANAGEMENT_URL = sys.argv[1]
GUARDIAN_MANAGEMENT_USER = sys.argv[2]
GUARDIAN_MANAGEMENT_PASSWORD = sys.argv[3]
KEYCLOAK_URL = sys.argv[4]
KEYCLOAK_CLIENT_ID = sys.argv[5]
CONDITION_DIR = sys.argv[6]

TIMEOUT = 10


@lru_cache(maxsize=1)
def get_token():
    print("Getting token")
    data = {
        "client_id": KEYCLOAK_CLIENT_ID,
        "username": GUARDIAN_MANAGEMENT_USER,
        "password": GUARDIAN_MANAGEMENT_PASSWORD,
        "grant_type": "password",
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(KEYCLOAK_URL, data=data, headers=headers, timeout=TIMEOUT)
    token = response.json()["access_token"]
    print("Token received")
    return token


def handle_status_code(response):
    if response.status_code == 400 and response.json() == {
        "detail": {"message": "An object with the given identifiers already exists."}
    }:
        return

    if not response.ok:
        print(response.json())
    response.raise_for_status()


def generate_headers():
    token = get_token()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    return headers


def create_app(app_name, display_name):
    headers = generate_headers()
    data = {"name": app_name, "display_name": display_name}
    response = requests.post(
        f"{GUARDIAN_MANAGEMENT_URL}/apps/register", headers=headers, json=data, timeout=TIMEOUT
    )
    handle_status_code(response)
    print(f"App '{app_name}' created:", response.json())


def create_namespace(app_name, namespace_name):
    headers = generate_headers()
    data = {"name": namespace_name}
    response = requests.post(
        f"{GUARDIAN_MANAGEMENT_URL}/namespaces/{app_name}", headers=headers, json=data, timeout=TIMEOUT
    )
    handle_status_code(response)
    print(f"Namespace '{namespace_name}' created:", response.json())


def create_role(app_name, namespace_name, role_name, display_name):
    headers = generate_headers()
    data = {"name": role_name, "display_name": display_name}
    response = requests.post(
        f"{GUARDIAN_MANAGEMENT_URL}/roles/{app_name}/{namespace_name}",
        headers=headers,
        json=data,
        timeout=TIMEOUT,
    )
    handle_status_code(response)
    print(f"Role '{role_name}' created:", response.json())


def create_permission(app_name, namespace_name, permission_name, display_name):
    headers = generate_headers()
    data = {"name": permission_name, "display_name": display_name}
    response = requests.post(
        f"{GUARDIAN_MANAGEMENT_URL}/permissions/{app_name}/{namespace_name}",
        headers=headers,
        json=data,
        timeout=TIMEOUT,
    )
    handle_status_code(response)
    print(f"Permission '{permission_name}' created:", response.json())


def create_condition(
    app_name, namespace_name, condition_name, display_name, documentation, code, parameters=None
):
    headers = generate_headers()
    if parameters is None:
        parameters = []
    data = {
        "name": condition_name,
        "display_name": display_name,
        "documentation": documentation,
        "parameters": parameters,
        "code": code,
    }
    response = requests.post(
        f"{GUARDIAN_MANAGEMENT_URL}/conditions/{app_name}/{namespace_name}",
        headers=headers,
        json=data,
        timeout=TIMEOUT,
    )
    handle_status_code(response)
    print(f"Condition '{condition_name}' created:", response.json())


def create_role_capability_mapping(
    name, display_name, app_name, namespace_name, role, permissions, conditions=None, relation="AND"
):
    headers = generate_headers()
    if conditions is None:
        conditions = []
    data = {
        "name": name,
        "display_name": display_name,
        "role": role,
        "conditions": conditions,
        "relation": relation,
        "permissions": [
            {"app_name": app_name, "namespace_name": namespace_name, "name": permission}
            for permission in permissions
        ],
    }
    response = requests.post(
        f"{GUARDIAN_MANAGEMENT_URL}/capabilities/{app_name}/{namespace_name}",
        headers=headers,
        json=data,
        timeout=TIMEOUT,
    )
    handle_status_code(response)
    print(f"Role-Capability-Mapping '{name}' created:", response.json())


def main():
    app_name = "ucsschool-user-management"
    default_namespace_name = "user-management"
    conditions_namespace_name = "conditions"
    roles = [
        ("student", "Student"),
        ("teacher", "Teacher"),
        ("school_admin", "School Administrator"),
        ("staff", "Staff"),
        ("super-admin", "Super Administrator"),
    ]
    permissions = [
        ("create-user", "Create User Action"),
        ("delete-user", "Delete User Action"),
        ("read-last_name", "Read Last Name"),
        ("read-first_name", "Read First Name"),
        ("read-disabled", "Read Disabled"),
        ("read-schools", "Read Schools"),
        ("read-school_classes", "Read School Classes"),
        ("read-roles", "Read Roles"),
        ("write-last_name", "Write Last Name"),
        ("write-first_name", "Write First Name"),
        ("write-username", "Write Username"),
        ("write-disabled", "Write Disabled"),
        ("write-schools", "Write Schools"),
        ("write-school_classes", "Write School Classes"),
        ("write-roles", "Write Roles"),
        ("write-password", "Write Password"),  # nosec B105
    ]

    print("Creating Guardian objects for UCS@school User Management")

    print("Creating App")
    create_app(app_name, "UCS@school User Management")

    print("Creating Namespaces")
    create_namespace(app_name, default_namespace_name)
    create_namespace(app_name, conditions_namespace_name)

    print("Creating Conditions")
    path_list = Path(CONDITION_DIR).glob("*.json")
    for data_file in path_list:
        with open(data_file, "r") as fd:
            cond_info = json.load(fd)
        cond_name = data_file.stem
        with open(Path(CONDITION_DIR) / f"{cond_name}.rego", "rb") as fd:
            code_raw = fd.read()
        create_condition(
            app_name,
            conditions_namespace_name,
            cond_name,
            cond_info["display_name"],
            cond_info["documentation"],
            base64.b64encode(code_raw).decode(),
            cond_info["parameters"],
        )

    print("Creating Roles")
    for role_name, display_name in roles:
        create_role(app_name, default_namespace_name, role_name, display_name)

    print("Creating Permissions")
    for permission_name, display_name in permissions:
        create_permission(app_name, default_namespace_name, permission_name, display_name)

    print("Creating Role-Capability-Mappings")
    create_role_capability_mapping(
        "super-admin_ucsschool-user-management",
        f"super-admin has all permissions in {app_name}:{default_namespace_name}",
        app_name,
        default_namespace_name,
        {"app_name": app_name, "namespace_name": default_namespace_name, "name": "super-admin"},
        [permission[0] for permission in permissions],
    )
    for role in ("student", "teacher", "staff", "school_admin"):
        create_role_capability_mapping(
            f"{role}-read-self",
            f"{role} can read their own fields",
            app_name,
            default_namespace_name,
            {"app_name": app_name, "namespace_name": default_namespace_name, "name": role},
            [
                f"read-{attr_name}"
                for attr_name in (
                    "last_name",
                    "first_name",
                    "disabled",
                    "schools",
                    "school_classes",
                    "roles",
                )
            ],
            conditions=[
                {
                    "app_name": "guardian",
                    "namespace_name": "builtin",
                    "name": "target_is_self",
                    "parameters": [],
                }
            ],
        )
    create_role_capability_mapping(
        "teacher-read-student",
        "Teachers can read student fields",
        app_name,
        default_namespace_name,
        {"app_name": app_name, "namespace_name": default_namespace_name, "name": "teacher"},
        [
            f"read-{attr_name}"
            for attr_name in (
                "last_name",
                "first_name",
                "disabled",
                "schools",
                "school_classes",
                "roles",
            )
        ],
        conditions=[
            {
                "app_name": "guardian",
                "namespace_name": "builtin",
                "name": "target_has_role_in_same_context",
                "parameters": [
                    {
                        "name": "role",
                        "value": "ucsschool-user-management:user-management:student",
                        "value_type": "ROLE",
                    }
                ],
            }
        ],
    )
    create_role_capability_mapping(
        "create-users-general",
        "Create Users (school level permission)",
        app_name,
        default_namespace_name,
        {"app_name": app_name, "namespace_name": default_namespace_name, "name": "school_admin"},
        [
            "create-user",
        ],
        conditions=[
            {
                "app_name": "guardian",
                "namespace_name": "builtin",
                "name": "target_has_role_in_same_context",
                "parameters": [
                    {
                        "name": "role",
                        "value": "ucsschool-user-management:user-management:school",
                    }
                ],
            },
        ],
    )
    create_role_capability_mapping(
        "create-users-in-same-school",
        "Create Users within same school",
        app_name,
        default_namespace_name,
        {"app_name": app_name, "namespace_name": default_namespace_name, "name": "school_admin"},
        [
            *[
                f"write-{attr_name}"
                for attr_name in (
                    "last_name",
                    "first_name",
                    "username",
                    "disabled",
                    "schools",
                    "school_classes",
                    "roles",
                    "password",
                )
            ],
            *[
                f"read-{attr_name}"
                for attr_name in (
                    "last_name",
                    "first_name",
                    "disabled",
                    "schools",
                    "school_classes",
                    "roles",
                )
            ],
            "create-user",
        ],
        conditions=[
            {
                "app_name": app_name,
                "namespace_name": conditions_namespace_name,
                "name": "action_is_creation",
                "parameters": [],
            },
            {
                "app_name": app_name,
                "namespace_name": conditions_namespace_name,
                "name": "target_will_be_in_same_school_only",
                "parameters": [],
            },
            {
                "app_name": app_name,
                "namespace_name": conditions_namespace_name,
                "name": "target_will_have_allowed_roles_only",
                "parameters": [
                    {
                        "name": "roles",
                        "value": f"{app_name}:{default_namespace_name}:student,{app_name}:{default_namespace_name}:teacher",
                    }
                ],
            },
        ],
    )
    create_role_capability_mapping(
        "administrate-users-in-same-school",
        "Administrate (edit,delete) users (teachers, students, staff) in same school.",
        app_name,
        default_namespace_name,
        {"app_name": app_name, "namespace_name": default_namespace_name, "name": "school_admin"},
        [
            *[
                f"write-{attr_name}"
                for attr_name in (
                    "last_name",
                    "first_name",
                    "username",
                    "disabled",
                    "school_classes",
                    "password",
                )
            ],
            *[
                f"read-{attr_name}"
                for attr_name in (
                    "schools",
                    "roles",
                )
            ],
            "delete-user",
        ],
        conditions=[
            {
                "app_name": "guardian",
                "namespace_name": "builtin",
                "name": "target_has_role_in_same_context",
                "parameters": [
                    {
                        "name": "role",
                        "value": f"{app_name}:{default_namespace_name}:{role}",
                    }
                ],
            }
            for role in ("student", "teacher", "staff")
        ],
        relation="OR",
    )

    print("All Guardian objects created")


if __name__ == "__main__":
    main()
