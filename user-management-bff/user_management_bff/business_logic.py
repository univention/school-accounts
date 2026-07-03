# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
from collections import defaultdict

from loguru import logger

from .api_models import AddUsersConfig, EditUsersConfig, UserCreateRequest
from .errors import NoSchoolUserError, ObjectNotFoundError, OperationNotSupportedError, PermissionsError
from .lang import _
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
    WorkGroup,
)
from .ports import (
    AddConfigRepresentationPort,
    EditConfigRepresentationPort,
    PermissionsPort,
    SchoolClassesPersistencePort,
    SchoolsPersistencePort,
    UserCreateRepresentation,
    UsersGetRepresentation,
    UsersPersistencePort,
    UsersRepresentationPort,
    WorkGroupsPersistencePort,
)
from .presentation import SchoolsData, UserListData
from .utils import (
    get_required_permissions_for_create_request,
    get_required_permissions_for_patch_request,
)


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


def school_to_target(school: School) -> Target:
    return Target(
        old_target=TargetObject(
            id=school.id, type=TargetObjectType.SCHOOL, attributes=school.model_dump()
        ),
        new_target=None,
    )


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


def user_create_request_to_target(user_create_request: UserCreateRequest) -> Target:
    user_attributes = user_create_request.model_dump(exclude={"school", "roles", "school_classes"})
    user_attributes["schools"] = [user_create_request.school]
    user_attributes["roles"] = [
        f"{role}:school:{user_create_request.school}" for role in user_create_request.roles
    ]
    user_attributes["school_classes"] = {user_create_request.school: user_create_request.school_classes}
    user_attributes["work_groups"] = {user_create_request.school: user_create_request.work_groups}
    target = Target(
        old_target=None,
        new_target=TargetObject(
            id=user_create_request.username, type=TargetObjectType.USER, attributes=user_attributes
        ),
    )
    return target


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
    school_classes = defaultdict(list)
    work_groups = defaultdict(list)
    for school in schools:
        school_classes[school.id].extend(await school_classes_get_adapter.get_school_classes(school.id))
        work_groups[school.id].extend(await work_groups_get_adapter.get_work_groups(school.id))
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
    return SchoolsData(schools=schools, permissions=permissions)


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
        if Permission.use_as_filter in permissions[school_class.id]
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
        if Permission.use_as_filter in permissions[work_group.id]
    ]


async def create_user(
    users_create_adapter: UsersPersistencePort,
    representation_port: UsersRepresentationPort[UsersGetRepresentation, UserCreateRepresentation],
    users_get_adapter: UsersPersistencePort,
    permissions_port: PermissionsPort,
    actor_id: str,
    request_data: UserCreateRequest,
    lang: str,
) -> UserCreateRepresentation:
    logger.debug(
        "Received request from actor to create user.", actor_id=actor_id, username=request_data.username
    )

    actor = await get_actor(actor_id, users_get_adapter, lang)
    permissions = await permissions_port.get_permissions(
        actor, [user_create_request_to_target(request_data)]
    )
    target_permissions = set(list(permissions.values())[0]) if permissions else set()
    missing_permissions = get_required_permissions_for_create_request(request_data) - target_permissions
    if len(missing_permissions) > 0:
        logger.warning(
            "Denied actor permission to create user.", actor_id=actor_id, username=request_data.username
        )
        raise PermissionsError(
            _("You do not have the permission to create this user.", lang=lang),
            missing_permissions=list(missing_permissions),
        )

    user = await users_create_adapter.create_user(request_data)
    logger.info("User created on behalf of actor.", actor_id=actor_id, username=user.id)
    return representation_port.create_user_representation(user, target_permissions)


async def delete_user(
    users_delete_adapter: UsersPersistencePort,
    permissions_port: PermissionsPort,
    actor_id: str,
    identifier: str,
    lang: str,
) -> None:
    logger.debug("Received request from actor to delete user.", actor_id=actor_id, user_id=identifier)

    actor = await get_actor(actor_id, users_delete_adapter, lang)
    try:
        user = await users_delete_adapter.get_user(identifier)
    except ObjectNotFoundError:
        logger.warning(
            "Actor requested to delete user, but the user does not exist.",
            actor_id=actor_id,
            user_id=identifier,
        )
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
        logger.warning("Denied actor permission to delete user.", actor_id=actor_id, user_id=identifier)
        raise PermissionsError(
            _("You do not have the permission to edit this user.", lang=lang),
            missing_permissions=[Permission.delete_user],
        )
    try:
        logger.info("User deleted on behalf of actor.", actor_id=actor_id, user_id=identifier)
        await users_delete_adapter.delete_user(identifier)
    except ObjectNotFoundError:
        logger.warning(
            "Deletion failed because user did not exist", actor_id=actor_id, identifier=identifier
        )
        return None  # we treat non existing users as successful deletion in the frontend


async def patch_user(
    users_patch_adapter: UsersPersistencePort,
    representation_port: UsersRepresentationPort[UsersGetRepresentation, UserCreateRepresentation],
    permissions_port: PermissionsPort,
    actor_id: str,
    patch_data: UserPatchRequest,
    lang: str,
) -> UserCreateRepresentation:
    logger.debug(
        "Received request from actor to update user.", actor_id=actor_id, user_id=patch_data.identifier
    )
    actor = await get_actor(actor_id, users_patch_adapter, lang)
    old_user = await users_patch_adapter.get_user(patch_data.identifier)
    new_user = old_user.model_copy(deep=True)
    if patch_data.school not in new_user.attributes.schools:
        user = patch_data.identifier
        school = patch_data.school
        logger.error(
            "Unable to update: User is not part of school {school}.",
            actor_id=actor_id,
            user_id=user,
            school=patch_data.school,
        )
        raise OperationNotSupportedError(
            _(
                "Cannot update user '{user}' in school '{school}'.".format(user=user, school=school),
                lang=lang,
            )
        )
    patch_attributes = patch_data.attributes.model_dump(exclude_unset=True, exclude={"school_classes"})
    if patch_data.attributes.activated is not None:
        patch_attributes["disabled"] = not patch_data.attributes.activated
        patch_attributes.pop("activated")

    for key, value in patch_attributes.items():
        setattr(new_user.attributes, key, value)
    if (
        "school_classes" in patch_data.attributes.model_fields_set
        and patch_data.attributes.school_classes is not None
    ):
        new_user.attributes.school_classes[patch_data.school] = patch_data.attributes.school_classes

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
                    id=new_user.id,
                    attributes=new_user.attributes.model_dump(),
                    type=TargetObjectType.USER,
                ),
            )
        ],
    )
    target_permissions = set(list(permissions.values())[0]) if permissions else set()
    missing_permissions = get_required_permissions_for_patch_request(patch_data) - target_permissions
    if len(missing_permissions) > 0:
        logger.warning(
            "Denied actor permission to update user.", actor_id=actor_id, user_id=patch_data.identifier
        )
        raise PermissionsError(
            _("You do not have the permission to edit this user.", lang=lang),
            missing_permissions=list(missing_permissions),
        )
    new_user = await users_patch_adapter.save_user(new_user)
    logger.info("Updated user on behalf of actor.", actor_id=actor_id, user_id=new_user.id)
    return representation_port.create_user_representation(new_user, target_permissions)


async def get_user_add_config(
    schools_get_port: SchoolsPersistencePort,
    school_classes_persistence_port: SchoolClassesPersistencePort,
    work_groups_persistence_port: WorkGroupsPersistencePort,
    representation_port: AddConfigRepresentationPort,
    school: str,
    lang: str,
) -> AddUsersConfig:
    logger.debug(f"Preparing user add config with school {school}.")
    try:
        school_obj = (await schools_get_port.get_schools(name=school))[0]
    except IndexError:
        logger.error("School object does not exist", school=school)
        raise ObjectNotFoundError(school)
    school_classes = await school_classes_persistence_port.get_school_classes(school)
    work_groups = await work_groups_persistence_port.get_work_groups(school)
    return representation_port.add_config_representation(school_obj, school_classes, work_groups, lang)


async def get_user_edit_config(
    users_get_port: UsersPersistencePort,
    user_representation_port: UsersRepresentationPort,
    schools_get_port: SchoolsPersistencePort,
    school_classes_persistence_port: SchoolClassesPersistencePort,
    work_groups_persistence_port: WorkGroupsPersistencePort,
    representation_port: EditConfigRepresentationPort,
    permissions_port: PermissionsPort,
    actor_id: str,
    user_id: str,
    school: str,
    lang: str,
) -> EditUsersConfig:

    logger.debug(
        "Preparing user edit config for user on behalf of actor", actor_id=actor_id, user_id=user_id
    )

    try:
        school_obj = (await schools_get_port.get_schools(name=school))[0]
    except IndexError:
        logger.error("School object does not exist.", actor_id=actor_id, school=school)
        raise ObjectNotFoundError(school)

    actor = await get_actor(actor_id, users_get_port, lang)
    user = await users_get_port.get_user(user_id)
    permissions = await permissions_port.get_permissions(
        actor,
        [
            Target(
                old_target=TargetObject(
                    id=user.id,
                    attributes={**user.attributes.model_dump(), "password": ""},
                    type=TargetObjectType.USER,
                ),
                new_target=TargetObject(
                    id=user.id,
                    attributes={**user.attributes.model_dump(), "password": ""},
                    type=TargetObjectType.USER,
                ),
            )
        ],
    )
    user_data = user_representation_port.edit_user_representation(user, set(permissions[user.id]))
    if not user_data.attributes.schools.value or school not in user_data.attributes.schools.value:
        logger.error("User is not part of school.", actor_id=actor_id, user_id=user_id, school=school)
        raise ObjectNotFoundError(f"{user_id}:{school}")

    school_classes = await school_classes_persistence_port.get_school_classes(school)
    work_groups = await work_groups_persistence_port.get_work_groups(school)

    return representation_port.edit_config_representation(
        user_data, school_obj, school_classes, work_groups, lang
    )
