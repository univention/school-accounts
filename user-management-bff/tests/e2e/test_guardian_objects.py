# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Any

import pytest
import requests


def _check(guardian_management_url: str, payload: dict[str, Any]) -> dict[str, dict[str, str]]:
    response = requests.post(f"{guardian_management_url}/api/check/resources", json=payload)
    assert response.status_code == 200
    return {result["resource"]["id"]: result["actions"] for result in response.json()["results"]}


@pytest.mark.e2e
def test_self_reads_own_data_not_someone_elses(guardian_management_url: str):
    actions = _check(
        guardian_management_url,
        {
            "requestId": "self-read",
            "principal": {
                "id": "alice",
                "roles": ["ucsschool:user"],
                "attr": {
                    "cerbos_roles": [{"name": "student", "context": "school1"}],
                    "school_classes": {},
                },
            },
            "resources": [
                {
                    "resource": {
                        "id": "alice",
                        "kind": "ucsschool:user",
                        "attr": {
                            "app_name": "ucsschool-user-management",
                            "old": {
                                "cerbos_roles": [{"name": "student", "context": "school1"}],
                                "school_classes": {},
                            },
                        },
                    },
                    "actions": ["read-first_name", "read-disabled"],
                },
                {
                    "resource": {
                        "id": "someone_else",
                        "kind": "ucsschool:user",
                        "attr": {
                            "app_name": "ucsschool-user-management",
                            "old": {
                                "cerbos_roles": [{"name": "student", "context": "school2"}],
                                "school_classes": {},
                            },
                        },
                    },
                    "actions": ["read-first_name"],
                },
            ],
        },
    )
    assert actions["alice"] == {"read-first_name": "EFFECT_ALLOW", "read-disabled": "EFFECT_ALLOW"}
    assert actions["someone_else"] == {"read-first_name": "EFFECT_DENY"}


@pytest.mark.e2e
def test_teacher_reads_and_resets_student_in_same_class_not_another_class(guardian_management_url: str):
    actions = _check(
        guardian_management_url,
        {
            "requestId": "teacher-class-scope",
            "principal": {
                "id": "bob",
                "roles": ["ucsschool:user"],
                "attr": {
                    "cerbos_roles": [{"name": "teacher", "context": "school1"}],
                    "school_classes": {"school1": ["1a"]},
                },
            },
            "resources": [
                {
                    "resource": {
                        "id": "student1",
                        "kind": "ucsschool:user",
                        "attr": {
                            "app_name": "ucsschool-user-management",
                            "old": {
                                "cerbos_roles": [{"name": "student", "context": "school1"}],
                                "school_classes": {"school1": ["1a"]},
                            },
                        },
                    },
                    "actions": ["read-first_name", "write-password"],
                },
                {
                    "resource": {
                        "id": "student2",
                        "kind": "ucsschool:user",
                        "attr": {
                            "app_name": "ucsschool-user-management",
                            "old": {
                                "cerbos_roles": [{"name": "student", "context": "school1"}],
                                "school_classes": {"school1": ["1b"]},
                            },
                        },
                    },
                    "actions": ["read-first_name", "write-password"],
                },
            ],
        },
    )
    assert actions["student1"] == {"read-first_name": "EFFECT_ALLOW", "write-password": "EFFECT_ALLOW"}
    assert actions["student2"] == {"read-first_name": "EFFECT_DENY", "write-password": "EFFECT_DENY"}


@pytest.mark.e2e
def test_school_admin_resets_passwords_in_school_except_another_school_admin(
    guardian_management_url: str,
):
    actions = _check(
        guardian_management_url,
        {
            "requestId": "school-admin-reset",
            "principal": {
                "id": "dave",
                "roles": ["ucsschool:user"],
                "attr": {
                    "cerbos_roles": [{"name": "school_admin", "context": "school1"}],
                    "school_classes": {},
                },
            },
            "resources": [
                {
                    "resource": {
                        "id": "teacher1",
                        "kind": "ucsschool:user",
                        "attr": {
                            "app_name": "ucsschool-user-management",
                            "old": {
                                "cerbos_roles": [{"name": "teacher", "context": "school1"}],
                                "school_classes": {},
                            },
                        },
                    },
                    "actions": ["write-password"],
                },
                {
                    "resource": {
                        "id": "admin2",
                        "kind": "ucsschool:user",
                        "attr": {
                            "app_name": "ucsschool-user-management",
                            "old": {
                                "cerbos_roles": [{"name": "school_admin", "context": "school1"}],
                                "school_classes": {},
                            },
                        },
                    },
                    "actions": ["write-password"],
                },
            ],
        },
    )
    assert actions["teacher1"] == {"write-password": "EFFECT_ALLOW"}
    assert actions["admin2"] == {"write-password": "EFFECT_DENY"}


@pytest.mark.e2e
def test_staff_reads_staff_data_but_cannot_reset_password(guardian_management_url: str):
    actions = _check(
        guardian_management_url,
        {
            "requestId": "staff-parity",
            "principal": {
                "id": "grace",
                "roles": ["ucsschool:user"],
                "attr": {
                    "cerbos_roles": [{"name": "staff", "context": "school1"}],
                    "school_classes": {},
                },
            },
            "resources": [
                {
                    "resource": {
                        "id": "staff1",
                        "kind": "ucsschool:user",
                        "attr": {
                            "app_name": "ucsschool-user-management",
                            "old": {
                                "cerbos_roles": [{"name": "staff", "context": "school1"}],
                                "school_classes": {},
                            },
                        },
                    },
                    "actions": ["read-birthday", "write-password"],
                },
            ],
        },
    )
    assert actions["staff1"] == {"read-birthday": "EFFECT_ALLOW", "write-password": "EFFECT_DENY"}


def _group_resource(kind: str, role: str, group_id: str, school: str) -> dict[str, Any]:
    """A class or work group target, shaped the way the BFF sends it.

    ``_target_object_to_guardian_object`` synthesises a role for every non-user
    target - ``school_class:school:<school>`` / ``workgroup:school:<school>`` -
    so these targets carry cerbos_roles alongside the school attribute. Leaving
    the roles out here would make the school_admin rules look broken.
    """
    return {
        "resource": {
            "id": group_id,
            "kind": kind,
            "attr": {
                "app_name": "ucsschool-user-management",
                "old": {"school": school, "cerbos_roles": [{"name": role, "context": school}]},
            },
        },
        "actions": ["use-as-filter"],
    }


def _school_resource(school_id: str) -> dict[str, Any]:
    """A school target. Its synthesised role is ``school:school:<id>``."""
    return {
        "resource": {
            "id": school_id,
            "kind": "ucsschool:school",
            "attr": {
                "app_name": "ucsschool-user-management",
                "old": {"cerbos_roles": [{"name": "school", "context": school_id}]},
            },
        },
        "actions": ["use-as-filter"],
    }


@pytest.mark.e2e
def test_school_class_filter_scoped_to_own_class(guardian_management_url: str):
    actions = _check(
        guardian_management_url,
        {
            "requestId": "class-filter-member",
            "principal": {
                "id": "bob",
                "roles": ["ucsschool:user"],
                "attr": {"cerbos_roles": [], "school_classes": {"school1": ["1a"]}},
            },
            "resources": [
                _group_resource("ucsschool:class", "school_class", "1a", "school1"),
                _group_resource("ucsschool:class", "school_class", "1b", "school1"),
            ],
        },
    )
    assert actions["1a"] == {"use-as-filter": "EFFECT_ALLOW"}
    assert actions["1b"] == {"use-as-filter": "EFFECT_DENY"}


@pytest.mark.e2e
def test_school_class_filter_for_school_admin_covers_the_whole_school(guardian_management_url: str):
    actions = _check(
        guardian_management_url,
        {
            "requestId": "class-filter-school-admin",
            "principal": {
                "id": "dave",
                "roles": ["ucsschool:user"],
                "attr": {
                    "cerbos_roles": [{"name": "school_admin", "context": "school1"}],
                    "school_classes": {},
                },
            },
            "resources": [
                _group_resource("ucsschool:class", "school_class", "1a", "school1"),
                _group_resource("ucsschool:class", "school_class", "2a", "school2"),
            ],
        },
    )
    # A school_admin is a member of no class, so this only passes via the
    # school_admin rule.
    assert actions["1a"] == {"use-as-filter": "EFFECT_ALLOW"}
    assert actions["2a"] == {"use-as-filter": "EFFECT_DENY"}


@pytest.mark.e2e
def test_work_group_filter_scoped_to_own_group(guardian_management_url: str):
    actions = _check(
        guardian_management_url,
        {
            "requestId": "work-group-filter-member",
            "principal": {
                "id": "bob",
                "roles": ["ucsschool:user"],
                "attr": {"cerbos_roles": [], "work_groups": {"school1": ["chess-club"]}},
            },
            "resources": [
                _group_resource("ucsschool:workgroup", "workgroup", "chess-club", "school1"),
                _group_resource("ucsschool:workgroup", "workgroup", "art-club", "school1"),
            ],
        },
    )
    assert actions["chess-club"] == {"use-as-filter": "EFFECT_ALLOW"}
    assert actions["art-club"] == {"use-as-filter": "EFFECT_DENY"}


@pytest.mark.e2e
def test_work_group_filter_for_school_admin_covers_the_whole_school(guardian_management_url: str):
    actions = _check(
        guardian_management_url,
        {
            "requestId": "work-group-filter-school-admin",
            "principal": {
                "id": "dave",
                "roles": ["ucsschool:user"],
                "attr": {
                    "cerbos_roles": [{"name": "school_admin", "context": "school1"}],
                    "work_groups": {},
                },
            },
            "resources": [
                _group_resource("ucsschool:workgroup", "workgroup", "chess-club", "school1"),
                _group_resource("ucsschool:workgroup", "workgroup", "robotics-club", "school2"),
            ],
        },
    )
    assert actions["chess-club"] == {"use-as-filter": "EFFECT_ALLOW"}
    assert actions["robotics-club"] == {"use-as-filter": "EFFECT_DENY"}


@pytest.mark.e2e
def test_school_filter_scoped_to_enrolled_schools(guardian_management_url: str):
    actions = _check(
        guardian_management_url,
        {
            "requestId": "school-filter",
            "principal": {
                "id": "bob",
                "roles": ["ucsschool:user"],
                # The school filter reads attr.schools, which _user_to_actor
                # always sends because it dumps all of UserAttributes.
                "attr": {
                    "cerbos_roles": [{"name": "student", "context": "school1"}],
                    "schools": ["school1"],
                },
            },
            "resources": [_school_resource("school1"), _school_resource("school2")],
        },
    )
    assert actions["school1"] == {"use-as-filter": "EFFECT_ALLOW"}
    assert actions["school2"] == {"use-as-filter": "EFFECT_DENY"}
