# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# Exercises the real CerbosPermissionsAdapter (domain objects in, mapped Permission
# dict out) against a live Cerbos server, using the same scenarios already locked in
# by dev/scripts/cerbos_check_examples.sh, which validates the raw wire shape; this
# validates that our domain-object -> Principal/Resource mapping actually produces
# the same policy decisions end to end.

import pytest

from ucsschool_accounts_bff.adapters.permissions import CerbosPermissionsAdapter
from ucsschool_accounts_bff.models import (
    Permission,
    Target,
    TargetObject,
    TargetObjectType,
    User,
    UserAttributes,
)


def _user(
    user_id: str,
    *,
    roles: list[str],
    school_classes: dict[str, list[str]] | None = None,
    schools: list[str] | None = None,
    work_groups: dict[str, list[str]] | None = None,
) -> User:
    return User(
        id=user_id,
        attributes=UserAttributes(
            last_name="Last",
            first_name="First",
            username=user_id,
            disabled=False,
            schools=schools or [],
            school_classes=school_classes or {},
            work_groups=work_groups or {},
            roles=roles,
        ),
    )


def _user_target(
    target_id: str,
    *,
    roles: list[str],
    school_classes: dict[str, list[str]] | None = None,
    legal_guardians: list[str] | None = None,
) -> Target:
    target_object = TargetObject(
        id=target_id,
        type=TargetObjectType.USER,
        attributes={
            "roles": roles,
            "school_classes": school_classes or {},
            "legal_guardians": legal_guardians or [],
        },
    )
    return Target(old_target=target_object, new_target=None)


def _school_class_target(target_id: str, *, school: str) -> Target:
    return Target(
        old_target=TargetObject(
            id=target_id, type=TargetObjectType.SCHOOL_CLASS, attributes={"school": school}
        ),
        new_target=None,
    )


def _school_target(target_id: str) -> Target:
    return Target(
        old_target=TargetObject(id=target_id, type=TargetObjectType.SCHOOL, attributes={}),
        new_target=None,
    )


def _work_group_target(target_id: str, *, school: str) -> Target:
    return Target(
        old_target=TargetObject(
            id=target_id, type=TargetObjectType.WORK_GROUP, attributes={"school": school}
        ),
        new_target=None,
    )


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_non_student_reads_own_data_not_someone_elses(cerbos_adapter: CerbosPermissionsAdapter):
    bob = _user("bob", roles=["teacher:school:school1"])
    permissions = await cerbos_adapter.get_permissions(
        bob,
        [
            _user_target("bob", roles=["teacher:school:school1"]),
            _user_target("someone_else", roles=["student:school:school2"]),
        ],
    )
    assert {Permission.read_first_name, Permission.read_disabled} <= set(permissions["bob"])
    assert Permission.write_password not in permissions["bob"]
    assert permissions["someone_else"] == []


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_student_has_no_capabilities_not_even_on_themselves(
    cerbos_adapter: CerbosPermissionsAdapter,
):
    alice = _user("alice", roles=["student:school:school1"])
    permissions = await cerbos_adapter.get_permissions(
        alice,
        [
            _user_target("alice", roles=["student:school:school1"]),
            _user_target("someone_else", roles=["student:school:school1"]),
        ],
    )
    assert permissions["alice"] == []
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
async def test_staff_has_no_capabilities_over_other_users(cerbos_adapter: CerbosPermissionsAdapter):
    grace = _user("grace", roles=["staff:school:school1"])
    permissions = await cerbos_adapter.get_permissions(
        grace,
        [
            _user_target("staff1", roles=["staff:school:school1"]),
            _user_target("teacher1", roles=["teacher:school:school1"]),
        ],
    )
    assert permissions["staff1"] == []
    assert permissions["teacher1"] == []


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_legal_guardian_reads_and_resets_ward_only(cerbos_adapter: CerbosPermissionsAdapter):
    # The legal_guardian role the directory service gives a guardian in their ward's
    # school grants nothing here; the legal_guardians attribute on the ward does.
    mallory = _user("mallory", roles=["legal_guardian:school:school2"])
    permissions = await cerbos_adapter.get_permissions(
        mallory,
        [
            _user_target("ward1", roles=["student:school:school2"], legal_guardians=["mallory"]),
            _user_target("ward2", roles=["student:school:school2"], legal_guardians=["trent"]),
        ],
    )
    assert {Permission.read_birthday, Permission.read_email, Permission.write_password} <= set(
        permissions["ward1"]
    )
    assert permissions["ward2"] == []


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_nobody_resets_the_password_of_a_school_admin(
    cerbos_adapter: CerbosPermissionsAdapter,
):
    # zoe holds school_admin at school2 while being a student at school1, so all
    # three routes reach her: bob teaches her class, dave administers school1, mary
    # is her guardian. school_admin has no matrix key, so each loses the password
    # and keeps the reads.
    zoe_target = _user_target(
        "zoe",
        roles=["student:school:school1", "school_admin:school:school2"],
        school_classes={"school1": ["1a"]},
        legal_guardians=["mary"],
    )
    actors = [
        _user("bob", roles=["teacher:school:school1"], school_classes={"school1": ["1a"]}),
        _user("dave", roles=["school_admin:school:school1"]),
        _user("mary", roles=["legal_guardian:school:school1"]),
    ]
    for actor in actors:
        permissions = await cerbos_adapter.get_permissions(actor, [zoe_target])
        assert Permission.write_password not in permissions["zoe"], actor.id
        assert Permission.read_first_name in permissions["zoe"], actor.id


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_school_admin_resets_password_of_user_enrolled_at_a_second_school(
    cerbos_adapter: CerbosPermissionsAdapter,
):
    # exists() over the target's roles, not all(): dave administers school1 only,
    # and that enrolment is enough. all() would deny every school_admin the reset of
    # anyone who is also something elsewhere - a moved pupil, commonly.
    frank = _user_target(
        "frank",
        roles=["student:school:school1", "student:school:school2"],
        school_classes={"school2": ["9z"]},
    )
    dave = _user("dave", roles=["school_admin:school:school1"])
    permissions = await cerbos_adapter.get_permissions(dave, [frank])
    assert Permission.write_password in permissions["frank"]


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_legal_guardian_resets_the_password_of_a_student_ward_only(
    cerbos_adapter: CerbosPermissionsAdapter,
):
    # The reads ignore the ward's roles; the reset needs student and nothing else.
    # Two student enrolments are still only a student, while no role at all is not a
    # student - that is what the size() guard in target_is_student_only is for.
    mallory = _user("mallory", roles=["legal_guardian:school:school2"])
    # ward id -> the roles it holds, and whether mallory may reset its password.
    wards: dict[str, tuple[list[str], bool]] = {
        "student": (["student:school:school2"], True),
        "student_at_two_schools": (["student:school:school1", "student:school:school2"], True),
        "student_and_staff": (["student:school:school2", "staff:school:school1"], False),
        "teacher": (["teacher:school:school2"], False),
        "no_role_at_all": ([], False),
    }
    permissions = await cerbos_adapter.get_permissions(
        mallory,
        [
            _user_target(ward_id, roles=roles, legal_guardians=["mallory"])
            for ward_id, (roles, _resettable) in wards.items()
        ],
    )
    for ward_id, (_roles, resettable) in wards.items():
        assert Permission.read_first_name in permissions[ward_id], ward_id
        assert (Permission.write_password in permissions[ward_id]) is resettable, ward_id


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_being_a_parent_does_not_protect_a_password_from_the_school_admin(
    cerbos_adapter: CerbosPermissionsAdapter,
):
    # Every guardian holds legal_guardian and the check is all() over the target's
    # roles, so it has to be a matrix key - without it every parent's password
    # would be protected from their own school_admin as well as from everyone
    # else. Being a key does not make it reachable by a teacher.
    staff_parent = _user_target(
        "parentstaff", roles=["staff:school:school1", "legal_guardian:school:school1"]
    )
    pupil_parent = _user_target(
        "parentpupil",
        roles=["student:school:school1", "legal_guardian:school:school1"],
        school_classes={"school1": ["1a"]},
    )
    dave = _user("dave", roles=["school_admin:school:school1"])
    bob = _user("bob", roles=["teacher:school:school1"], school_classes={"school1": ["1a"]})

    admin_permissions = await cerbos_adapter.get_permissions(dave, [staff_parent, pupil_parent])
    assert Permission.write_password in admin_permissions["parentstaff"]
    assert Permission.write_password in admin_permissions["parentpupil"]

    # The teacher reaches neither: the guardian role is resettable by a
    # school_admin alone, and one of them is not a student at all.
    teacher_permissions = await cerbos_adapter.get_permissions(bob, [staff_parent, pupil_parent])
    assert Permission.write_password not in teacher_permissions["parentpupil"]
    assert Permission.read_first_name in teacher_permissions["parentpupil"]
    assert teacher_permissions["parentstaff"] == []


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_a_reset_needs_authority_over_every_role_the_target_holds(
    cerbos_adapter: CerbosPermissionsAdapter,
):
    # A teacher may reset students and nothing else, so a pupil who holds a
    # second role is out of their teacher's reach, even in the teacher's own
    # class. staff and legal_guardian grant their holder nothing and still
    # protect them this way - only a school_admin can reset those.
    bob = _user("bob", roles=["teacher:school:school1"], school_classes={"school1": ["1a"]})
    dave = _user("dave", roles=["school_admin:school:school1"])
    in_class = {"school1": ["1a"]}
    targets = {
        "pupil": (["student:school:school1"], True),
        "pupil_who_is_staff": (["student:school:school1", "staff:school:school1"], False),
        "pupil_who_is_guardian": (
            ["student:school:school1", "legal_guardian:school:school1"],
            False,
        ),
        "pupil_who_teaches": (["student:school:school1", "teacher:school:school1"], False),
        "staff_only": (["staff:school:school1"], False),
    }
    resources = [
        _user_target(name, roles=roles, school_classes=in_class)
        for name, (roles, _resettable) in targets.items()
    ]

    teacher_permissions = await cerbos_adapter.get_permissions(bob, resources)
    for name, (_roles, resettable) in targets.items():
        assert (Permission.write_password in teacher_permissions[name]) is resettable, name

    # The school_admin reaches all of them.
    admin_permissions = await cerbos_adapter.get_permissions(dave, resources)
    for name in targets:
        assert Permission.write_password in admin_permissions[name], name


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_nobody_resets_their_own_password(cerbos_adapter: CerbosPermissionsAdapter):
    # judy teaches the class she is enrolled in, so the student/teacher cell
    # matches her teacher role against her own student role. The is_self guard is
    # the only thing that denies the reset.
    judy = _user(
        "judy",
        roles=["teacher:school:school1", "student:school:school1"],
        school_classes={"school1": ["1a"]},
    )
    permissions = await cerbos_adapter.get_permissions(
        judy,
        [
            _user_target(
                "judy",
                roles=["teacher:school:school1", "student:school:school1"],
                school_classes={"school1": ["1a"]},
            )
        ],
    )
    assert {Permission.read_first_name, Permission.read_email} <= set(permissions["judy"])
    assert Permission.write_password not in permissions["judy"]


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_teacher_who_is_a_student_at_another_school_reads_own_data(
    cerbos_adapter: CerbosPermissionsAdapter,
):
    eve = _user("eve", roles=["teacher:school:school1", "student:school:school2"])
    permissions = await cerbos_adapter.get_permissions(
        eve,
        [_user_target("eve", roles=["teacher:school:school1", "student:school:school2"])],
    )
    assert {Permission.read_first_name, Permission.read_roles} <= set(permissions["eve"])
    assert Permission.write_password not in permissions["eve"]


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_user_without_any_school_role_gets_no_permissions(
    cerbos_adapter: CerbosPermissionsAdapter,
):
    # The directory service gives every user a role, so no <role>:school:<ou> string
    # at all means something upstream is broken. Such a user gets nothing, not even
    # their own record - an empty role list must not read as "not a student".
    quinn = _user("quinn", roles=[])
    permissions = await cerbos_adapter.get_permissions(
        quinn,
        [
            _user_target("quinn", roles=[]),
            _user_target("pupil", roles=["student:school:school1"]),
        ],
    )
    assert permissions["quinn"] == []
    assert permissions["pupil"] == []


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


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_school_admin_class_filter_scoped_to_own_school(
    cerbos_adapter: CerbosPermissionsAdapter,
):
    dave = _user("dave", roles=["school_admin:school:school1"])
    permissions = await cerbos_adapter.get_permissions(
        dave,
        [
            _school_class_target("1a", school="school1"),
            _school_class_target("2a", school="school2"),
        ],
    )
    assert permissions["1a"] == [Permission.use_as_filter]
    assert permissions["2a"] == []


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_school_filter_scoped_to_enrolled_school(cerbos_adapter: CerbosPermissionsAdapter):
    bob = _user("bob", roles=["student:school:school1"], schools=["school1"])
    permissions = await cerbos_adapter.get_permissions(
        bob, [_school_target("school1"), _school_target("school2")]
    )
    assert permissions["school1"] == [Permission.use_as_filter]
    assert permissions["school2"] == []


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_work_group_filter_scoped_to_own_group(cerbos_adapter: CerbosPermissionsAdapter):
    bob = _user("bob", roles=[], work_groups={"school1": ["chess-club"]})
    permissions = await cerbos_adapter.get_permissions(
        bob,
        [
            _work_group_target("chess-club", school="school1"),
            _work_group_target("art-club", school="school1"),
        ],
    )
    assert permissions["chess-club"] == [Permission.use_as_filter]
    assert permissions["art-club"] == []
