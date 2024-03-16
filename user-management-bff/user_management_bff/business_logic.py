# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from loguru import logger

from .api_models import UserCreateRequest
from .errors import NoSchoolUserError, ObjectNotFoundError
from .models import School, Target, TargetObject, TargetObjectType, UsersGetRequest
from .ports import (
    PermissionsPort,
    SchoolsGetRepresentation,
    SchoolsPersistencePort,
    SchoolsRepresentationPort,
    UserCreateRepresentation,
    UsersGetRepresentation,
    UsersPersistencePort,
    UsersRepresentationPort,
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
    representation_port: UsersRepresentationPort[UsersGetRepresentation, UserCreateRepresentation],
    request_data: UsersGetRequest,
) -> UsersGetRepresentation:
    users = await users_get_adapter.get_users(request_data.school)
    return representation_port.create_users_representation(users)


async def get_schools(
    schools_get_adapter: SchoolsPersistencePort,
    representation_port: SchoolsRepresentationPort[SchoolsGetRepresentation],
    permissions_port: PermissionsPort,
    users_get_adapter: UsersPersistencePort,
    actor_id: str,
) -> SchoolsGetRepresentation:
    try:
        actor = await users_get_adapter.get_user(actor_id)
    except ObjectNotFoundError as exc:
        raise NoSchoolUserError(
            f"The logged in user '{exc.identifier}' is not a valid UCS@school user.",
            identifier=exc.identifier,
        ) from exc
    schools = await schools_get_adapter.get_schools()
    permissions = await permissions_port.get_permissions(
        actor, [school_to_target(school) for school in schools]
    )
    return representation_port.create_schools_representation(schools, permissions)


async def create_user(
    users_create_adapter: UsersPersistencePort,
    representation_port: UsersRepresentationPort[UsersGetRepresentation, UserCreateRepresentation],
    request_data: UserCreateRequest,
) -> UserCreateRepresentation:
    user = await users_create_adapter.create_user(request_data)
    return representation_port.create_user_representation(user)


async def delete_user(users_delete_adapter: UsersPersistencePort, identifier: str) -> None:
    try:
        await users_delete_adapter.delete_user(identifier)
    except ObjectNotFoundError:
        logger.warning("Deletion failed because user did not exist", identifier=identifier)
        return None  # we treat non existing users as successful deletion in the frontend
