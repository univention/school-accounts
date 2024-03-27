# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from loguru import logger

from .api_models import UserCreateRequest
from .errors import NoSchoolUserError, ObjectNotFoundError, OperationNotSupportedError, PermissionsError
from .models import (
    Permission,
    School,
    SchoolClass,
    Target,
    TargetObject,
    TargetObjectType,
    User,
    UserPatchRequest,
    UsersGetRequest,
)
from .ports import (
    PermissionsPort,
    SchoolClassesPersistencePort,
    SchoolsGetRepresentation,
    SchoolsPersistencePort,
    SchoolsRepresentationPort,
    UserCreateRepresentation,
    UsersGetRepresentation,
    UsersPersistencePort,
    UsersRepresentationPort,
)
from .utils import (
    get_required_permissions_for_create_request,
    get_required_permissions_for_patch_request,
)


async def get_actor(actor_id: str, users_persistence_adapter: UsersPersistencePort) -> User:
    try:
        return await users_persistence_adapter.get_user(actor_id)
    except ObjectNotFoundError as exc:
        raise NoSchoolUserError(
            f"The logged in user '{exc.identifier}' is not a valid UCS@school user.",
            identifier=exc.identifier,
        ) from exc


def school_to_target(school: School) -> Target:
    return Target(
        old_target=TargetObject(
            id=school.id, type=TargetObjectType.SCHOOL, attributes=school.model_dump()
        ),
        new_target=None,
    )


def user_create_request_to_target(user_create_request: UserCreateRequest) -> Target:
    user_attributes = user_create_request.model_dump(exclude={"school", "roles", "school_classes"})
    user_attributes["schools"] = [user_create_request.school]
    user_attributes["roles"] = [
        f"{role}:school:{user_create_request.school}" for role in user_create_request.roles
    ]
    user_attributes["school_classes"] = {user_create_request.school: user_create_request.school_classes}
    target = Target(
        old_target=None,
        new_target=TargetObject(
            id=user_create_request.username, type=TargetObjectType.USER, attributes=user_attributes
        ),
    )
    return target


async def get_users(
    users_get_adapter: UsersPersistencePort,
    representation_port: UsersRepresentationPort[UsersGetRepresentation, UserCreateRepresentation],
    permissions_port: PermissionsPort,
    actor_id: str,
    request_data: UsersGetRequest,
) -> UsersGetRepresentation:
    actor = await get_actor(actor_id, users_get_adapter)
    users = await users_get_adapter.get_users(request_data.school)
    permissions = await permissions_port.get_permissions(
        actor,
        [
            Target(old_target=target_object, new_target=target_object)
            for user in users
            if (
                target_object := TargetObject(
                    id=user.id, type=TargetObjectType.USER, attributes=user.attributes.model_dump()
                )
            )
        ],
    )
    return representation_port.create_users_representation(users, permissions)


async def get_user(
    users_get_adapter: UsersPersistencePort,
    representation_port: UsersRepresentationPort[UsersGetRepresentation, UserCreateRepresentation],
    permissions_port: PermissionsPort,
    actor_id: str,
    user_id: str,
) -> UserCreateRepresentation:
    actor = await get_actor(actor_id, users_get_adapter)
    user = await users_get_adapter.get_user(user_id)
    permissions = await permissions_port.get_permissions(
        actor,
        [
            Target(
                old_target=TargetObject(
                    id=user.id, attributes=user.attributes.model_dump(), type=TargetObjectType.USER
                ),
                new_target=None,
            )
        ],
    )
    return representation_port.create_user_representation(user, set(permissions[user.id]))


async def get_schools(
    schools_get_adapter: SchoolsPersistencePort,
    representation_port: SchoolsRepresentationPort[SchoolsGetRepresentation],
    permissions_port: PermissionsPort,
    users_get_adapter: UsersPersistencePort,
    actor_id: str,
) -> SchoolsGetRepresentation:
    actor = await get_actor(actor_id, users_get_adapter)
    schools = await schools_get_adapter.get_schools()
    permissions = await permissions_port.get_permissions(
        actor, [school_to_target(school) for school in schools]
    )
    return representation_port.create_schools_representation(schools, permissions)


async def create_user(
    users_create_adapter: UsersPersistencePort,
    representation_port: UsersRepresentationPort[UsersGetRepresentation, UserCreateRepresentation],
    users_get_adapter: UsersPersistencePort,
    permissions_port: PermissionsPort,
    actor_id: str,
    request_data: UserCreateRequest,
) -> UserCreateRepresentation:
    actor = await get_actor(actor_id, users_get_adapter)
    permissions = await permissions_port.get_permissions(
        actor, [user_create_request_to_target(request_data)]
    )
    target_permissions = set(list(permissions.values())[0]) if permissions else set()
    missing_permissions = get_required_permissions_for_create_request(request_data) - target_permissions
    if len(missing_permissions) > 0:
        raise PermissionsError(
            "You do not have the permission to create this user.",
            missing_permissions=list(missing_permissions),
        )

    user = await users_create_adapter.create_user(request_data)
    return representation_port.create_user_representation(user, target_permissions)


async def delete_user(
    users_delete_adapter: UsersPersistencePort,
    permissions_port: PermissionsPort,
    actor_id: str,
    identifier: str,
) -> None:
    actor = await get_actor(actor_id, users_delete_adapter)
    try:
        user = await users_delete_adapter.get_user(identifier)
    except ObjectNotFoundError:
        return  # We treat a not found user as a successful deletion
    permissions = await permissions_port.get_permissions(
        actor,
        [
            Target(
                old_target=TargetObject(
                    id=user.id, attributes=user.attributes.model_dump(), type=TargetObjectType.USER
                ),
                new_target=None,
            )
        ],
    )
    target_permissions = set(list(permissions.values())[0]) if permissions else set()
    if Permission.delete_user not in target_permissions:
        raise PermissionsError(
            "You do not have the permission to edit this user.",
            missing_permissions=[Permission.delete_user],
        )
    try:
        await users_delete_adapter.delete_user(identifier)
    except ObjectNotFoundError:
        logger.warning("Deletion failed because user did not exist", identifier=identifier)
        return None  # we treat non existing users as successful deletion in the frontend


async def patch_user(
    users_patch_adapter: UsersPersistencePort,
    representation_port: UsersRepresentationPort[UsersGetRepresentation, UserCreateRepresentation],
    permissions_port: PermissionsPort,
    actor_id: str,
    patch_data: UserPatchRequest,
) -> UserCreateRepresentation:
    actor = await get_actor(actor_id, users_patch_adapter)
    old_user = await users_patch_adapter.get_user(patch_data.identifier)
    user = old_user.model_copy(deep=True)
    if patch_data.school not in user.attributes.schools:
        raise OperationNotSupportedError(
            f"Cannot patch user '{patch_data.identifier}' in school '{patch_data.school}'."
        )
    patch_attributes = patch_data.attributes.model_dump(exclude_unset=True, exclude={"school_classes"})
    if patch_data.attributes.active is not None:
        patch_attributes["disabled"] = not patch_data.attributes.active
        patch_attributes.pop("active")
    for key, value in patch_attributes.items():
        setattr(user.attributes, key, value)
    if (
        "school_classes" in patch_data.attributes.model_fields_set
        and patch_data.attributes.school_classes is not None
    ):
        user.attributes.school_classes[patch_data.school] = patch_data.attributes.school_classes
    permissions = await permissions_port.get_permissions(
        actor,
        [
            Target(
                old_target=TargetObject(
                    id=old_user.id,
                    attributes=old_user.attributes.model_dump(),
                    type=TargetObjectType.USER,
                ),
                new_target=TargetObject(
                    id=user.id, attributes=user.attributes.model_dump(), type=TargetObjectType.USER
                ),
            )
        ],
    )
    target_permissions = set(list(permissions.values())[0]) if permissions else set()
    missing_permissions = get_required_permissions_for_patch_request(patch_data) - target_permissions
    if len(missing_permissions) > 0:
        raise PermissionsError(
            "You do not have the permission to edit this user.",
            missing_permissions=list(missing_permissions),
        )
    user = await users_patch_adapter.save_user(user)
    return representation_port.create_user_representation(user, target_permissions)


async def get_user_add_config_data(
    school_classes_persistence_port: SchoolClassesPersistencePort,
    permissions_port: PermissionsPort,
    actor_id: str,
    school: str,
) -> list[SchoolClass]:
    return await school_classes_persistence_port.get_school_classes(school)
