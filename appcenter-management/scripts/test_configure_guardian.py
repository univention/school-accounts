#!/usr/bin/env python3.7
# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Script to test the configuration of guardian for the user-management app."""


import requests
import sys
from functools import lru_cache
from operator import itemgetter

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
    data = {
        "client_id": KEYCLOAK_CLIENT_ID,
        "username": GUARDIAN_MANAGEMENT_USER,
        "password": GUARDIAN_MANAGEMENT_PASSWORD,
        "grant_type": "password",
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(KEYCLOAK_URL, data=data, headers=headers, timeout=TIMEOUT)
    token = response.json()["access_token"]
    return token


def generate_headers():
    token = get_token()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    return headers


def get_capabilities(app_name, namespace_name, name):
    headers = generate_headers()
    response = requests.get(
        f"{GUARDIAN_MANAGEMENT_URL}/capabilities/{app_name}/{namespace_name}/{name}",
        headers=headers,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def test_capabilities():
    app_name = "ucsschool-user-management"
    namespace_name = "user-management"

    capabilities = get_capabilities(app_name, namespace_name, "super-admin")
    assert capabilities["capability"]["app_name"] == "user-management", "wrong app_name"
    assert sorted(capabilities["capability"]["permissions"], key=itemgetter("name")) == sorted(
        [
            {"app_name": "user-management", "namespace_name": "user-management", "name": "read-schools"},
            {"app_name": "user-management", "namespace_name": "user-management", "name": "read-role"},
            {
                "app_name": "user-management",
                "namespace_name": "user-management",
                "name": "read-lastname",
            },
            {
                "app_name": "user-management",
                "namespace_name": "user-management",
                "name": "read-username",
            },
            {
                "app_name": "user-management",
                "namespace_name": "user-management",
                "name": "read-activation-state",
            },
            {
                "app_name": "user-management",
                "namespace_name": "user-management",
                "name": "read-data-for-all-schools",
            },
            {
                "app_name": "user-management",
                "namespace_name": "user-management",
                "name": "read-firstname",
            },
        ],
        key=itemgetter("name"),
    ), "wrong permissions"


def main():
    test_capabilities()


if __name__ == "__main__":
    main()
