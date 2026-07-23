# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import pytest
import requests


@pytest.mark.e2e
def test_guardian_conditions(access_token, guardian_management_url):
    token = access_token("Administrator", "univention")
    response = requests.get(
        f"{guardian_management_url}/conditions/ucsschool-user-management",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert sorted(response.json()) == sorted(
        {
            "pagination": {"offset": 0, "limit": 3, "total_count": 3},
            "conditions": [
                {
                    "app_name": "ucsschool-user-management",
                    "namespace_name": "conditions",
                    "name": "action_is_creation",
                    "display_name": "Only if action is creation",
                    "resource_url": "https://primary.ucsschool.test/guardian/management/conditions/"
                    "ucsschool-user-management/conditions/action_is_creation",
                    "documentation": "True if the old target is null or empty.",
                    "parameters": [],
                },
                {
                    "app_name": "ucsschool-user-management",
                    "namespace_name": "conditions",
                    "name": "target_will_be_in_same_school_only",
                    "display_name": "Only if target will be in the same school",
                    "resource_url": "https://primary.ucsschool.test/guardian/management/conditions/"
                    "ucsschool-user-management/conditions/target_will_be_in_same_school_only",
                    "documentation": "True if the new target has only roles in the school of the "
                    "actors' role.",
                    "parameters": [],
                },
                {
                    "app_name": "ucsschool-user-management",
                    "namespace_name": "conditions",
                    "name": "target_will_have_allowed_roles_only",
                    "display_name": "Only if target will have only the allowed roles",
                    "resource_url": "https://primary.ucsschool.test/guardian/management/conditions/"
                    "ucsschool-user-management/conditions/target_will_have_allowed_roles_only",
                    "documentation": "True if the new target has only roles that are specified "
                    "in the roles "
                    "parameter. Roles should be separated by ','",
                    "parameters": [{"name": "roles", "value_type": "STRING"}],
                },
            ],
        }
    )


@pytest.mark.e2e
def test_guardian_permissions(access_token, guardian_management_url):
    token = access_token("Administrator", "univention")
    response = requests.get(
        f"{guardian_management_url}/permissions/ucsschool-user-management",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert sorted(response.json()) == sorted(
        {
            "pagination": {"offset": 0, "limit": 15, "total_count": 15},
            "permissions": [
                {
                    "app_name": "ucsschool-user-management",
                    "namespace_name": "user-management",
                    "name": "create-user",
                    "display_name": "Create User Action",
                    "resource_url": "https://primary.ucsschool.test/guardian/management/permissions/"
                    "ucsschool-user-management/user-management/create-user",
                },
                {
                    "app_name": "ucsschool-user-management",
                    "namespace_name": "user-management",
                    "name": "read-activation-state",
                    "display_name": "Read Activation State",
                    "resource_url": "https://primary.ucsschool.test/guardian/management/permissions/"
                    "ucsschool-user-management/user-management/read-activation-state",
                },
                {
                    "app_name": "ucsschool-user-management",
                    "namespace_name": "user-management",
                    "name": "read-data-for-all-schools",
                    "display_name": "Read Data for All Schools",
                    "resource_url": "https://primary.ucsschool.test/guardian/management/permissions/"
                    "ucsschool-user-management/user-management/read-data-for-all-schools",
                },
                {
                    "app_name": "ucsschool-user-management",
                    "namespace_name": "user-management",
                    "name": "read-firstname",
                    "display_name": "Read First Name",
                    "resource_url": "https://primary.ucsschool.test/guardian/management/permissions/"
                    "ucsschool-user-management/user-management/read-firstname",
                },
                {
                    "app_name": "ucsschool-user-management",
                    "namespace_name": "user-management",
                    "name": "read-lastname",
                    "display_name": "Read Last Name",
                    "resource_url": "https://primary.ucsschool.test/guardian/management/permissions/"
                    "ucsschool-user-management/user-management/read-lastname",
                },
                {
                    "app_name": "ucsschool-user-management",
                    "namespace_name": "user-management",
                    "name": "read-role",
                    "display_name": "Read Role",
                    "resource_url": "https://primary.ucsschool.test/guardian/management/permissions/"
                    "ucsschool-user-management/user-management/read-role",
                },
                {
                    "app_name": "ucsschool-user-management",
                    "namespace_name": "user-management",
                    "name": "read-schools",
                    "display_name": "Read Schools",
                    "resource_url": "https://primary.ucsschool.test/guardian/management/permissions/"
                    "ucsschool-user-management/user-management/read-schools",
                },
                {
                    "app_name": "ucsschool-user-management",
                    "namespace_name": "user-management",
                    "name": "write-activation-state",
                    "display_name": "Write Activation State",
                    "resource_url": "https://primary.ucsschool.test/guardian/management/permissions/"
                    "ucsschool-user-management/user-management/write-activation-state",
                },
                {
                    "app_name": "ucsschool-user-management",
                    "namespace_name": "user-management",
                    "name": "write-data-for-all-schools",
                    "display_name": "Write Data for All Schools",
                    "resource_url": "https://primary.ucsschool.test/guardian/management/permissions/"
                    "ucsschool-user-management/user-management/write-data-for-all-schools",
                },
                {
                    "app_name": "ucsschool-user-management",
                    "namespace_name": "user-management",
                    "name": "write-firstname",
                    "display_name": "Write First Name",
                    "resource_url": "https://primary.ucsschool.test/guardian/management/permissions/"
                    "ucsschool-user-management/user-management/write-firstname",
                },
                {
                    "app_name": "ucsschool-user-management",
                    "namespace_name": "user-management",
                    "name": "write-lastname",
                    "display_name": "Write Last Name",
                    "resource_url": "https://primary.ucsschool.test/guardian/management/permissions/"
                    "ucsschool-user-management/user-management/write-lastname",
                },
                {
                    "app_name": "ucsschool-user-management",
                    "namespace_name": "user-management",
                    "name": "write-password",
                    "display_name": "Write Password",
                    "resource_url": "https://primary.ucsschool.test/guardian/management/permissions/"
                    "ucsschool-user-management/user-management/write-password",
                },
                {
                    "app_name": "ucsschool-user-management",
                    "namespace_name": "user-management",
                    "name": "write-role",
                    "display_name": "Write Role",
                    "resource_url": "https://primary.ucsschool.test/guardian/management/permissions/"
                    "ucsschool-user-management/user-management/write-role",
                },
                {
                    "app_name": "ucsschool-user-management",
                    "namespace_name": "user-management",
                    "name": "write-schools",
                    "display_name": "Write Schools",
                    "resource_url": "https://primary.ucsschool.test/guardian/management/permissions/"
                    "ucsschool-user-management/user-management/write-schools",
                },
                {
                    "app_name": "ucsschool-user-management",
                    "namespace_name": "user-management",
                    "name": "write-username",
                    "display_name": "Write Username",
                    "resource_url": "https://primary.ucsschool.test/guardian/management/permissions/"
                    "ucsschool-user-management/user-management/write-username",
                },
            ],
        }
    )


@pytest.mark.e2e
def test_guardian_capabilities(access_token, guardian_management_url):
    token = access_token("Administrator", "univention")
    response = requests.get(
        f"{guardian_management_url}/capabilities/ucsschool-user-management/user-management",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert sorted(response.json()) == sorted(
        {
            "pagination": {"offset": 0, "limit": 7, "total_count": 7},
            "capabilities": [
                {
                    "app_name": "ucsschool-user-management",
                    "namespace_name": "user-management",
                    "name": "create-users-in-same-school",
                    "display_name": "Create Users within same school",
                    "resource_url": "https://primary.ucsschool.test/guardian/management/capabilities/"
                    "ucsschool-user-management/user-management/create-users-in-same-school",
                    "role": {
                        "app_name": "ucsschool-user-management",
                        "namespace_name": "user-management",
                        "name": "school-admin",
                    },
                    "conditions": [
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "conditions",
                            "name": "target_will_have_allowed_roles_only",
                            "parameters": [
                                {
                                    "name": "roles",
                                    "value": "ucsschool-user-management:user-management:student,"
                                    "ucsschool-user-management:user-management:teacher",
                                    "value_type": "STRING",
                                }
                            ],
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "conditions",
                            "name": "target_will_be_in_same_school_only",
                            "parameters": [],
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "conditions",
                            "name": "action_is_creation",
                            "parameters": [],
                        },
                    ],
                    "relation": "AND",
                    "permissions": [
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "write-schools",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "write-role",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "create-user",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-lastname",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "write-password",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "write-username",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-firstname",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-schools",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "write-firstname",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-activation-state",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-role",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "write-activation-state",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "write-lastname",
                        },
                    ],
                },
                {
                    "app_name": "ucsschool-user-management",
                    "namespace_name": "user-management",
                    "name": "school-admin-read-self",
                    "display_name": "school-admin can read their own fields",
                    "resource_url": "https://primary.ucsschool.test/guardian/management/capabilities/"
                    "ucsschool-user-management/user-management/school-admin-read-self",
                    "role": {
                        "app_name": "ucsschool-user-management",
                        "namespace_name": "user-management",
                        "name": "school-admin",
                    },
                    "conditions": [
                        {
                            "app_name": "guardian",
                            "namespace_name": "builtin",
                            "name": "target_is_self",
                            "parameters": [],
                        }
                    ],
                    "relation": "AND",
                    "permissions": [
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-lastname",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-firstname",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-activation-state",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-role",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-schools",
                        },
                    ],
                },
                {
                    "app_name": "ucsschool-user-management",
                    "namespace_name": "user-management",
                    "name": "staff-read-self",
                    "display_name": "staff can read their own fields",
                    "resource_url": "https://primary.ucsschool.test/guardian/management/capabilities/"
                    "ucsschool-user-management/user-management/staff-read-self",
                    "role": {
                        "app_name": "ucsschool-user-management",
                        "namespace_name": "user-management",
                        "name": "staff",
                    },
                    "conditions": [
                        {
                            "app_name": "guardian",
                            "namespace_name": "builtin",
                            "name": "target_is_self",
                            "parameters": [],
                        }
                    ],
                    "relation": "AND",
                    "permissions": [
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-firstname",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-schools",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-activation-state",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-role",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-lastname",
                        },
                    ],
                },
                {
                    "app_name": "ucsschool-user-management",
                    "namespace_name": "user-management",
                    "name": "student-read-self",
                    "display_name": "student can read their own fields",
                    "resource_url": "https://primary.ucsschool.test/guardian/management/capabilities/"
                    "ucsschool-user-management/user-management/student-read-self",
                    "role": {
                        "app_name": "ucsschool-user-management",
                        "namespace_name": "user-management",
                        "name": "student",
                    },
                    "conditions": [
                        {
                            "app_name": "guardian",
                            "namespace_name": "builtin",
                            "name": "target_is_self",
                            "parameters": [],
                        }
                    ],
                    "relation": "AND",
                    "permissions": [
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-firstname",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-schools",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-activation-state",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-role",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-lastname",
                        },
                    ],
                },
                {
                    "app_name": "ucsschool-user-management",
                    "namespace_name": "user-management",
                    "name": "super-admin_ucsschool-user-management",
                    "display_name": "super-admin has all permissions in "
                    "ucsschool-user-management:user-management",
                    "resource_url": "https://primary.ucsschool.test/guardian/management/capabilities/"
                    "ucsschool-user-management/user-management/super-admin_ucsschool-user-management",
                    "role": {
                        "app_name": "ucsschool-user-management",
                        "namespace_name": "user-management",
                        "name": "super-admin",
                    },
                    "conditions": [],
                    "relation": "AND",
                    "permissions": [
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "create-user",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "write-role",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "write-schools",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "write-lastname",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-lastname",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "write-activation-state",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "write-password",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-firstname",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-schools",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "write-username",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "write-data-for-all-schools",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "write-firstname",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-role",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-data-for-all-schools",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-activation-state",
                        },
                    ],
                },
                {
                    "app_name": "ucsschool-user-management",
                    "namespace_name": "user-management",
                    "name": "teacher-create-user",
                    "display_name": "Teacher can create users",
                    "resource_url": "https://primary.ucsschool.test/guardian/management/capabilities/"
                    "ucsschool-user-management/user-management/teacher-create-user",
                    "role": {
                        "app_name": "ucsschool-user-management",
                        "namespace_name": "user-management",
                        "name": "teacher",
                    },
                    "conditions": [],
                    "relation": "AND",
                    "permissions": [
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "create-user",
                        }
                    ],
                },
                {
                    "app_name": "ucsschool-user-management",
                    "namespace_name": "user-management",
                    "name": "teacher-read-self",
                    "display_name": "teacher can read their own fields",
                    "resource_url": "https://primary.ucsschool.test/guardian/management/capabilities/"
                    "ucsschool-user-management/user-management/teacher-read-self",
                    "role": {
                        "app_name": "ucsschool-user-management",
                        "namespace_name": "user-management",
                        "name": "teacher",
                    },
                    "conditions": [
                        {
                            "app_name": "guardian",
                            "namespace_name": "builtin",
                            "name": "target_is_self",
                            "parameters": [],
                        }
                    ],
                    "relation": "AND",
                    "permissions": [
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-lastname",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-firstname",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-schools",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-role",
                        },
                        {
                            "app_name": "ucsschool-user-management",
                            "namespace_name": "user-management",
                            "name": "read-activation-state",
                        },
                    ],
                },
            ],
        }
    )
