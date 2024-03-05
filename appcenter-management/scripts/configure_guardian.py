#!/usr/bin/env python3.7
# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Script to create the necessary Guardian objects fot the User management App.


* Apps:
  * ucsschool
* Namespaces:
  * user-management
* Roles:
  * student
  * teacher
  * school-admin
  * staff
  * super-admin
* Permissions:
  * read-lastname
  * read-firstname
  * read-username
  * read-schools
  * read-data-for-all-schools
  * read-activation-state
  * read-role
* Role-Capability-Mapping:
  * ucsschool:user-management:super-admin has all permissions listed above
"""


import requests
import sys
from functools import lru_cache

if len(sys.argv) != 6:
    print(
        f"Usage: {sys.argv[0]} <management_url> <username> <password> <keycloak_url> <keycloak_client>"
    )
    sys.exit(1)

GUARDIAN_MANAGEMENT_URL = sys.argv[1]
GUARDIAN_MANAGEMENT_USER = sys.argv[2]
GUARDIAN_MANAGEMENT_PASSWORD = sys.argv[3]
KEYCLOAK_URL = sys.argv[4]
KEYCLOAK_CLIENT_ID = sys.argv[5]

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


def create_role_capability_mapping(name, display_name, app_name, namespace_name, role, permissions):
    headers = generate_headers()
    data = {
        "name": name,
        "display_name": display_name,
        "role": role,
        "conditions": [],
        "relation": "AND",
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
    namespace_name = "user-management"
    roles = [
        ("student", "Student"),
        ("teacher", "Teacher"),
        ("school-admin", "School Administrator"),
        ("staff", "Staff"),
        ("super-admin", "Super Administrator"),
    ]
    permissions = [
        ("read-lastname", "Read Last Name"),
        ("read-firstname", "Read First Name"),
        ("read-username", "Read Username"),
        ("read-schools", "Read Schools"),
        ("read-data-for-all-schools", "Read Data for All Schools"),
        ("read-activation-state", "Read Activation State"),
        ("read-role", "Read Role"),
        ("create-user", "Create User Action"),
    ]

    print("Creating Guardian objects for UCS@school User Management")

    print("Creating App")
    create_app(app_name, "UCS@school User Management")

    print("Creating Namespace")
    create_namespace(app_name, namespace_name)

    print("Creating Roles")
    for role_name, display_name in roles:
        create_role(app_name, namespace_name, role_name, display_name)

    print("Creating Permissions")
    for permission_name, display_name in permissions:
        create_permission(app_name, namespace_name, permission_name, display_name)

    print("Creating Role-Capability-Mappings")
    create_role_capability_mapping(
        "super-admin_ucsschool-user-management",
        f"super-admin has all permissions in {app_name}:{namespace_name}",
        app_name,
        namespace_name,
        {"app_name": app_name, "namespace_name": namespace_name, "name": "super-admin"},
        [permission[0] for permission in permissions],
    )
    create_role_capability_mapping(
        "teacher-create-user",
        "Teacher can create users",
        app_name,
        namespace_name,
        {"app_name": app_name, "namespace_name": namespace_name, "name": "teacher"},
        ["create-user"],
    )

    print("All Guardian objects created")


if __name__ == "__main__":
    main()
