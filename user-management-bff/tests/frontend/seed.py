# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""The directory contents the frontend tests assert on, and how to put them there.

Against the compose dev stack the File adapters already serve `dev/data`, so
nothing here runs. Against an installed system there is no telling what the
directory holds, so the suite seeds its own objects through Kelvin and asserts
on those instead -- which is what lets it be pointed at any test machine that
has the app, rather than only at one seeded by hand.

The people are the `dev/data` ones, names and roles unchanged, so both paths
assert on the same usernames. The school is not: `dev/data`'s schools are
scenery for the dev stack, and Kelvin exposes no DELETE on `/schools/`
(confirmed against Kelvin 4.0.2), so every OU this creates stays on the machine
for good. One short, obviously test-owned OU is a defensible thing to leave
behind; ten German school names are not.

Nothing is torn down afterwards, and that is deliberate rather than laziness.
Deleting a user and creating it again under the same name leaves Keycloak's LDAP
federation holding a stale record for it, and every later login as that name is
rejected with "The authentication has failed" while a name Keycloak has never
seen logs in immediately -- measured on UCS 5.2 with the two created seconds
apart in this same OU. Since the OU is permanent anyway, its contents may as
well be: seeding reconciles what is there instead, so a machine converges on
this set and stays there, and repeat runs cost a handful of requests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ucsschool.kelvin.client import (
    NoObject,
    School,
    SchoolClass,
    SchoolClassResource,
    SchoolResource,
    Session,
    User,
    UserResource,
    WorkGroup,
    WorkGroupResource,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

SCHOOL = "umtest"
SCHOOL_DISPLAY_NAME = "User Management Test School"
SCHOOL_CLASS = "10b"
WORK_GROUP = "Erste-Hilfe-AG"
PASSWORD = "umtest.Password.2026"


@dataclass(frozen=True)
class SeedUser:
    """One `dev/data` person, in the terms Kelvin takes them in.

    `roles` are Kelvin's own role names; Kelvin derives the
    `school_admin:school:umtest` form from them, and that derived form is what
    the UI renders (see `adapters/users.py`).
    """

    name: str
    firstname: str
    lastname: str
    roles: list[str]
    school_classes: list[str] = field(default_factory=list[str])
    in_work_group: bool = False


LOGIN_USER = SeedUser("dev", "Dev", "Admin", ["school_admin"], in_work_group=True)
LISTED_USER = SeedUser("jonas.huber", "Jonas", "Huber", ["teacher"], [SCHOOL_CLASS], in_work_group=True)
USERS = (
    LOGIN_USER,
    LISTED_USER,
    SeedUser("maria.kaiser", "Maria", "Kaiser", ["teacher"], [SCHOOL_CLASS]),
    SeedUser("oskar.wagner", "Oskar", "Wagner", ["student"], [SCHOOL_CLASS]),
)


def _session(credentials: Mapping[str, str]) -> Session:
    # A test machine serves Kelvin under its own CA, which the dev container has
    # no reason to carry.
    return Session(**credentials, verify=False)  # pyright: ignore[reportArgumentType]


async def _ensure_school(session: Session) -> None:
    try:
        await SchoolResource(session=session).get(name=SCHOOL)
        return
    except NoObject:
        pass
    school = School(name=SCHOOL, display_name=SCHOOL_DISPLAY_NAME, session=session)
    await school.save()


async def _ensure_school_class(session: Session) -> None:
    try:
        await SchoolClassResource(session=session).get(school=SCHOOL, name=SCHOOL_CLASS)
        return
    except NoObject:
        pass
    school_class = SchoolClass(name=SCHOOL_CLASS, school=SCHOOL, users=[], session=session)
    await school_class.save()


async def _ensure_work_group(session: Session) -> None:
    try:
        await WorkGroupResource(session=session).get(school=SCHOOL, name=WORK_GROUP)
        return
    except NoObject:
        pass
    work_group = WorkGroup(name=WORK_GROUP, school=SCHOOL, users=[], session=session)
    await work_group.save()


async def _ensure_user(session: Session, seed_user: SeedUser) -> None:
    school_classes = {SCHOOL: seed_user.school_classes} if seed_user.school_classes else {}
    try:
        user = await UserResource(session=session).get(name=seed_user.name)
    except NoObject:
        user = User(
            name=seed_user.name,
            firstname=seed_user.firstname,
            lastname=seed_user.lastname,
            record_uid=seed_user.name,
            school=SCHOOL,
            schools=[SCHOOL],
            roles=seed_user.roles,
            school_classes=school_classes,
            password=PASSWORD,
            session=session,
        )
        await user.save()
        return
    # Reconcile rather than recreate, so an edit to this file reaches a machine
    # that already carries an older version of the same person. The password is
    # set on creation only: UCS's password history rejects setting the same one
    # again, which would fail every run after the first.
    user.firstname = seed_user.firstname
    user.lastname = seed_user.lastname
    user.school = SCHOOL
    user.schools = [SCHOOL]
    user.roles = seed_user.roles
    user.school_classes = school_classes
    await user.save()


async def _ensure_work_group_members(session: Session) -> None:
    """Membership is set from the group, not the user.

    This client's `User` carries `school_classes` but no work-group field at all,
    so a `work_groups=` argument is swallowed by its `**kwargs` and the member
    list stays empty without anything failing.
    """
    work_group = await WorkGroupResource(session=session).get(school=SCHOOL, name=WORK_GROUP)
    members = sorted(user.name for user in USERS if user.in_work_group)
    if sorted(work_group.users or []) == members:
        return
    work_group.users = members
    await work_group.save()


async def provision(credentials: Mapping[str, str]) -> None:
    async with _session(credentials) as session:
        await _ensure_school(session)
        await _ensure_school_class(session)
        await _ensure_work_group(session)
        for seed_user in USERS:
            await _ensure_user(session, seed_user)
        await _ensure_work_group_members(session)
