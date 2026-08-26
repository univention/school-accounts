# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import asyncio
from collections import defaultdict

from loguru import logger

from .constants import PASSWORD_RESET_MAX_CONCURRENCY, PASSWORD_RESET_MAX_TARGETS
from .errors import NoSchoolUserError, ObjectNotFoundError, PasswordResetRejectedError
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
from .presentation import (
    PasswordResetOutcome,
    PasswordResetOutcomeCode,
    PasswordResetRequestError,
    PasswordResetResultData,
    SchoolsData,
    UserListData,
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


def user_to_target(user: User) -> Target:
    target_object = TargetObject(
        id=user.id,
        type=TargetObjectType.USER,
        attributes=user.attributes.model_dump(),
    )
    return Target(
        old_target=target_object,
        new_target=target_object,
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

    permissions = await permissions_port.get_permissions(
        actor,
        [user_to_target(user) for user in users],
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


async def _fetch_targets(
    users_adapter: UsersPersistencePort, target_ids: list[str]
) -> tuple[dict[str, Target], list[PasswordResetOutcome]]:
    semaphore = asyncio.Semaphore(PASSWORD_RESET_MAX_CONCURRENCY)

    async def _fetch(target_id: str) -> Target:
        async with semaphore:
            return user_to_target(await users_adapter.get_user(target_id))

    # return_exceptions=True, then handle ourselves: without it, gather propagates
    # the first exception while other in-flight fetches keep running in the background
    # (mirrors CerbosPermissionsAdapter.get_permissions's rationale for the same pattern).
    # A missing target is an anticipated, per-user outcome; anything else is systemic
    # (e.g. a real connection error) and still aborts the whole call.
    results = await asyncio.gather(*(_fetch(tid) for tid in target_ids), return_exceptions=True)
    targets: dict[str, Target] = {}
    outcomes: list[PasswordResetOutcome] = []
    for target_id, result in zip(target_ids, results, strict=False):
        if isinstance(result, ObjectNotFoundError):
            outcomes.append(
                PasswordResetOutcome(target_id=target_id, outcome=PasswordResetOutcomeCode.not_found)
            )
        elif isinstance(result, BaseException):
            raise result
        else:
            targets[target_id] = result
    return targets, outcomes


async def _write_passwords(
    users_adapter: UsersPersistencePort, target_ids: list[str], password: str, actor_id: str
) -> list[PasswordResetOutcome]:
    semaphore = asyncio.Semaphore(PASSWORD_RESET_MAX_CONCURRENCY)

    async def _write(target_id: str) -> PasswordResetOutcome:
        async with semaphore:
            outcome, reason = PasswordResetOutcomeCode.success, None
            try:
                await users_adapter.set_password(target_id, password)
            except ObjectNotFoundError:
                outcome = PasswordResetOutcomeCode.not_found
            except PasswordResetRejectedError as exc:
                outcome, reason = PasswordResetOutcomeCode.rejected, exc.message
            logger.info(
                "Password reset outcome for target.",
                actor_id=actor_id,
                target_id=target_id,
                outcome=outcome,
                **({"reason": reason} if reason else {}),
            )
            return PasswordResetOutcome(target_id=target_id, outcome=outcome, reason=reason)

    return await asyncio.gather(*(_write(tid) for tid in target_ids))


async def set_passwords(
    users_adapter: UsersPersistencePort,
    permissions_port: PermissionsPort,
    actor_id: str,
    target_ids: list[str],
    password: str,
    lang: str,
) -> PasswordResetResultData:
    deduped_ids = list(dict.fromkeys(target_ids))
    logger.debug(
        "Resetting passwords for a selection of users.",
        actor_id=actor_id,
        target_count=len(deduped_ids),
    )
    if not deduped_ids:
        return PasswordResetResultData(outcomes=[], request_error=PasswordResetRequestError.no_targets)
    if len(deduped_ids) > PASSWORD_RESET_MAX_TARGETS:
        logger.warning(
            "Rejected a bulk password reset: selection exceeds the maximum target count.",
            actor_id=actor_id,
            target_count=len(deduped_ids),
            max_targets=PASSWORD_RESET_MAX_TARGETS,
        )
        return PasswordResetResultData(
            outcomes=[], request_error=PasswordResetRequestError.too_many_targets
        )
    if not password:
        logger.warning(
            "Rejected a bulk password reset: no password was supplied.",
            actor_id=actor_id,
            target_count=len(deduped_ids),
        )
        return PasswordResetResultData(
            outcomes=[], request_error=PasswordResetRequestError.empty_password
        )

    actor = await get_actor(actor_id, users_adapter, lang)
    targets_by_id, outcomes_list = await _fetch_targets(users_adapter, deduped_ids)
    outcomes: dict[str, PasswordResetOutcome] = {o.target_id: o for o in outcomes_list}

    permissions = await permissions_port.get_permissions(actor, list(targets_by_id.values()))
    permitted_ids = [
        tid for tid in targets_by_id if Permission.write_password in permissions.get(tid, [])
    ]
    denied_ids = [tid for tid in targets_by_id if tid not in permitted_ids]
    for tid in denied_ids:
        logger.warning(
            "Denied a password reset: actor lacks write-password on this target.",
            actor_id=actor_id,
            target_id=tid,
        )
        outcomes[tid] = PasswordResetOutcome(
            target_id=tid, outcome=PasswordResetOutcomeCode.permission_denied
        )

    for outcome in await _write_passwords(users_adapter, permitted_ids, password, actor_id):
        outcomes[outcome.target_id] = outcome

    return PasswordResetResultData(outcomes=[outcomes[tid] for tid in deduped_ids])
