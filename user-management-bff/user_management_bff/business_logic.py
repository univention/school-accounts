# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
from collections import defaultdict

from loguru import logger

from .errors import NoSchoolUserError, ObjectNotFoundError
from .lang import _
from .models import (
    Permission,
    School,
    SchoolClass,
    Target,
    TargetObject,
    TargetObjectType,
    User,
    UsersGetRequest,
    WorkGroup,
)
from .ports import (
    PermissionsPort,
    SchoolClassesPersistencePort,
    SchoolsPersistencePort,
    UsersPersistencePort,
    WorkGroupsPersistencePort,
)
from .presentation import SchoolsData, UserListData


async def get_actor(
    actor_id: str,
    users_persistence_adapter: UsersPersistencePort,
    lang: str,
) -> User:
    try:
        return await users_persistence_adapter.get_user(actor_id)
    except ObjectNotFoundError as exc:
        user = exc.identifier
        logger.error("Actor is not a valid UCS@school user.", actor_id=actor_id)
        raise NoSchoolUserError(
            _(
                "The logged in user '{user}' is not a valid UCS@school user.".format(user=user),
                lang=lang,
            ),
            identifier=exc.identifier,
        ) from exc


def school_class_to_target(school_class: SchoolClass) -> Target:
    return Target(
        old_target=TargetObject(
            id=school_class.id, type=TargetObjectType.SCHOOL_CLASS, attributes=school_class.model_dump()
        ),
        new_target=None,
    )


def work_group_to_target(work_group: WorkGroup) -> Target:
    return Target(
        old_target=TargetObject(
            id=work_group.id, type=TargetObjectType.WORK_GROUP, attributes=work_group.model_dump()
        ),
        new_target=None,
    )


def school_to_target(school: School) -> Target:
    return Target(
        old_target=TargetObject(
            id=school.id, type=TargetObjectType.SCHOOL, attributes=school.model_dump()
        ),
        new_target=None,
    )


async def get_users(
    users_get_adapter: UsersPersistencePort,
    schools_get_adapter: SchoolsPersistencePort,
    school_classes_get_adapter: SchoolClassesPersistencePort,
    work_groups_get_adapter: WorkGroupsPersistencePort,
    permissions_port: PermissionsPort,
    actor_id: str,
    request_data: UsersGetRequest,
    lang: str,
) -> UserListData:
    logger.debug("Retrieving all users of a school.", actor_id=actor_id, school=request_data.school)
    actor = await get_actor(actor_id, users_get_adapter, lang)
    users = await users_get_adapter.get_users(
        request_data.school, request_data.school_classes, request_data.work_groups
    )
    schools = await schools_get_adapter.get_schools()
    school_classes: defaultdict[str, list[SchoolClass]] = defaultdict(list)
    work_groups: defaultdict[str, list[WorkGroup]] = defaultdict(list)
    for school in schools:
        school_classes[school.id].extend(await school_classes_get_adapter.get_school_classes(school.id))
        work_groups[school.id].extend(await work_groups_get_adapter.get_work_groups(school.id))

    def make_target(user: User) -> Target:
        target_object = TargetObject(
            id=user.id,
            type=TargetObjectType.USER,
            attributes=user.attributes.model_dump(),
        )
        return Target(
            old_target=target_object,
            new_target=target_object,
        )

    permissions = await permissions_port.get_permissions(
        actor,
        [make_target(user) for user in users],
    )
    return UserListData(
        users=users,
        schools=schools,
        school_classes=dict(school_classes),
        work_groups=dict(work_groups),
        permissions=permissions,
    )


async def get_schools(
    schools_get_adapter: SchoolsPersistencePort,
    permissions_port: PermissionsPort,
    users_get_adapter: UsersPersistencePort,
    actor_id: str,
    lang: str,
) -> SchoolsData:
    logger.debug("Retrieving all schools.", actor_id=actor_id)
    actor = await get_actor(actor_id, users_get_adapter, lang)
    schools = await schools_get_adapter.get_schools()
    permissions = await permissions_port.get_permissions(
        actor, [school_to_target(school) for school in schools]
    )
    return SchoolsData(
        schools=[
            school for school in schools if Permission.use_as_filter in permissions.get(school.id, [])
        ]
    )


async def get_school_classes(
    schools_get_adapter: SchoolClassesPersistencePort,
    permissions_port: PermissionsPort,
    users_get_adapter: UsersPersistencePort,
    actor_id: str,
    school_id: str,
    lang: str,
) -> list[SchoolClass]:
    logger.debug("Retrieving all school classes.", actor_id=actor_id)
    actor = await get_actor(actor_id, users_get_adapter, lang)
    school_classes = await schools_get_adapter.get_school_classes(school_id)
    permissions = await permissions_port.get_permissions(
        actor, [school_class_to_target(school_class) for school_class in school_classes]
    )
    return [
        school_class
        for school_class in school_classes
        if Permission.use_as_filter in permissions.get(school_class.id, [])
    ]


async def get_work_groups(
    schools_get_adapter: WorkGroupsPersistencePort,
    permissions_port: PermissionsPort,
    users_get_adapter: UsersPersistencePort,
    actor_id: str,
    school_id: str,
    lang: str,
) -> list[WorkGroup]:
    logger.debug("Retrieving all work groups.", actor_id=actor_id)
    actor = await get_actor(actor_id, users_get_adapter, lang)
    work_groups = await schools_get_adapter.get_work_groups(school_id)
    permissions = await permissions_port.get_permissions(
        actor, [work_group_to_target(work_group) for work_group in work_groups]
    )
    return [
        work_group
        for work_group in work_groups
        if Permission.use_as_filter in permissions.get(work_group.id, [])
    ]
