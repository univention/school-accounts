# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Seeds the frontend test data through Kelvin, for runs given `--kelvin_url`.

Users are reconciled, never deleted: Keycloak rejects every login as a user that
was deleted and re-created under the same name.
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
    # No password: UCS's password history rejects setting the same one again.
    user.firstname = seed_user.firstname
    user.lastname = seed_user.lastname
    user.school = SCHOOL
    user.schools = [SCHOOL]
    user.roles = seed_user.roles
    user.school_classes = school_classes
    await user.save()


async def _ensure_work_group_members(session: Session) -> None:
    """The client's `User` has no work-group field; `work_groups=` would vanish into `**kwargs`."""
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
