# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# Exercises the real CerbosPermissionsAdapter (domain objects in, mapped Permission
# dict out) against a live Cerbos server, using the same scenarios already locked in
# by dev/scripts/cerbos_check_examples.sh and test_guardian_objects.py. Those two
# validate the raw wire shape; this validates that our domain-object -> Principal/
# Resource mapping actually produces the same policy decisions end to end.

import pytest
import pytest_asyncio

from user_management_bff.adapters.permissions import (
    CerbosPermissionsAdapter,
    CerbosPermissionsAdapterSettings,
)
from user_management_bff.models import (
    Permission,
    Target,
    TargetObject,
    TargetObjectType,
    User,
    UserAttributes,
)


def _user(user_id: str, *, roles: list[str], school_classes: dict[str, list[str]] | None = None) -> User:
    return User(
        id=user_id,
        attributes=UserAttributes(
            last_name="Last",
            first_name="First",
            username=user_id,
            disabled=False,
            schools=[],
            school_classes=school_classes or {},
            work_groups={},
            roles=roles,
        ),
    )


def _user_target(
    target_id: str, *, roles: list[str], school_classes: dict[str, list[str]] | None = None
) -> Target:
    target_object = TargetObject(
        id=target_id,
        type=TargetObjectType.USER,
        attributes={"roles": roles, "school_classes": school_classes or {}},
    )
    return Target(old_target=target_object, new_target=None)


def _school_class_target(target_id: str, *, school: str) -> Target:
    return Target(
        old_target=TargetObject(
            id=target_id, type=TargetObjectType.SCHOOL_CLASS, attributes={"school": school}
        ),
        new_target=None,
    )


@pytest_asyncio.fixture  # pyright: ignore[reportUnknownMemberType, reportUntypedFunctionDecorator]
async def cerbos_adapter(guardian_management_url: str) -> CerbosPermissionsAdapter:
    adapter = CerbosPermissionsAdapter()
    await adapter.configure(
        CerbosPermissionsAdapterSettings(cerbos_target=guardian_management_url, tls_verify=False)
    )
    return adapter


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_self_reads_own_data_not_someone_elses(cerbos_adapter: CerbosPermissionsAdapter):
    alice = _user("alice", roles=["student:school:school1"])
    permissions = await cerbos_adapter.get_permissions(
        alice,
        [
            _user_target("alice", roles=["student:school:school1"]),
            _user_target("someone_else", roles=["student:school:school2"]),
        ],
    )
    assert {Permission.read_first_name, Permission.read_disabled} <= set(permissions["alice"])
    assert permissions["someone_else"] == []


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_teacher_reads_and_resets_student_in_same_class_not_another_class(
    cerbos_adapter: CerbosPermissionsAdapter,
):
    bob = _user("bob", roles=["teacher:school:school1"], school_classes={"school1": ["1a"]})
    permissions = await cerbos_adapter.get_permissions(
        bob,
        [
            _user_target(
                "student1", roles=["student:school:school1"], school_classes={"school1": ["1a"]}
            ),
            _user_target(
                "student2", roles=["student:school:school1"], school_classes={"school1": ["1b"]}
            ),
        ],
    )
    assert {Permission.read_first_name, Permission.write_password} <= set(permissions["student1"])
    assert permissions["student2"] == []


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_school_admin_resets_passwords_in_school_except_another_school_admin(
    cerbos_adapter: CerbosPermissionsAdapter,
):
    dave = _user("dave", roles=["school_admin:school:school1"])
    permissions = await cerbos_adapter.get_permissions(
        dave,
        [
            _user_target("teacher1", roles=["teacher:school:school1"]),
            _user_target("admin2", roles=["school_admin:school:school1"]),
        ],
    )
    assert Permission.write_password in permissions["teacher1"]
    assert Permission.write_password not in permissions["admin2"]


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_staff_reads_teacher_data_but_cannot_reset_password(
    cerbos_adapter: CerbosPermissionsAdapter,
):
    grace = _user("grace", roles=["staff:school:school1"])
    permissions = await cerbos_adapter.get_permissions(
        grace, [_user_target("teacher1", roles=["teacher:school:school1"])]
    )
    assert Permission.read_birthday in permissions["teacher1"]
    assert Permission.write_password not in permissions["teacher1"]


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_school_class_filter_scoped_to_own_class(cerbos_adapter: CerbosPermissionsAdapter):
    bob = _user("bob", roles=[], school_classes={"school1": ["1a"]})
    permissions = await cerbos_adapter.get_permissions(
        bob,
        [
            _school_class_target("1a", school="school1"),
            _school_class_target("1b", school="school1"),
        ],
    )
    assert permissions["1a"] == [Permission.use_as_filter]
    assert permissions["1b"] == []
