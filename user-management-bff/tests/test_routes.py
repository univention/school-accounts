# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only


def test_get_users_config(test_client, api_prefix):
    response = test_client.get(f"{api_prefix}/config-users")
    assert response.status_code == 200
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
