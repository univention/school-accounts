# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import asyncio
from collections import Counter
from typing import Protocol, TypeVar

from loguru import logger

from .constants import PASSWORD_RESET_MAX_CONCURRENCY, PASSWORD_RESET_MAX_TARGETS
from .errors import (
    NoSchoolUserError,
    ObjectNotFoundError,
    PasswordChangeOnNextLoginUnsupportedError,
    PasswordResetRejectedError,
)
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
    PasswordResetSelectionData,
    SchoolsData,
    UserListData,
)


class _HasId(Protocol):
    id: str


_Filterable = TypeVar("_Filterable", bound=_HasId)


def _usable_as_filter(
    items: list[_Filterable], permissions: dict[str, list[Permission]], **context: object
) -> list[_Filterable]:
    permitted = [item for item in items if Permission.use_as_filter in permissions.get(item.id, [])]
    logger.debug(
        "Filtered by the use-as-filter permission.",
        fetched_count=len(items),
        permitted_count=len(permitted),
        **context,
    )
    return permitted


async def get_actor(
    actor_id: str,
    users_persistence_adapter: UsersPersistencePort,
    lang: str,
) -> User:
    try:
        actor = await users_persistence_adapter.get_user(actor_id)
    except ObjectNotFoundError as exc:
        user = exc.identifier
        logger.warning(
            "Actor is not a UCS@school user, so this module is unusable for them. "
            "Assign a UCS@school role, or use a school account.",
            actor_id=actor_id,
        )
        raise NoSchoolUserError(
            _(
                "The logged in user '{user}' is not a valid UCS@school user.",
                lang=lang,
            ).format(user=user),
            identifier=exc.identifier,
        ) from exc
    logger.debug(
        "Resolved the actor.",
        actor_id=actor_id,
        roles=actor.attributes.roles,
        schools=actor.attributes.schools,
    )
    return actor


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


async def _fetch_groups(
    school_classes_get_adapter: SchoolClassesPersistencePort,
    work_groups_get_adapter: WorkGroupsPersistencePort,
    schools: set[str],
) -> tuple[dict[str, list[SchoolClass]], dict[str, list[WorkGroup]]]:
    async def _fetch(school: str) -> tuple[str, list[SchoolClass], list[WorkGroup]]:
        classes, groups = await asyncio.gather(
            school_classes_get_adapter.get_school_classes(school),
            work_groups_get_adapter.get_work_groups(school),
        )
        return school, classes, groups

    fetched = await asyncio.gather(*(_fetch(school) for school in sorted(schools)))
    school_classes: dict[str, list[SchoolClass]] = {}
    work_groups: dict[str, list[WorkGroup]] = {}
    for school, classes, groups in fetched:
        school_classes[school] = classes
        work_groups[school] = groups
    return school_classes, work_groups


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
    actor = await get_actor(actor_id, users_get_adapter, lang)
    users = await users_get_adapter.get_users(
        request_data.school, request_data.school_classes, request_data.work_groups
    )
    schools = await schools_get_adapter.get_schools()
    school_classes, work_groups = await _fetch_groups(
        school_classes_get_adapter,
        work_groups_get_adapter,
        {
            school
            for user in users
            for school in (*user.attributes.school_classes, *user.attributes.work_groups)
        },
    )
    logger.debug(
        "Loaded the group names needed to render the list.",
        schools_scanned=len(school_classes),
        school_class_count=sum(len(items) for items in school_classes.values()),
        work_group_count=sum(len(items) for items in work_groups.values()),
    )

    permissions = await permissions_port.get_permissions(
        actor,
        [user_to_target(user) for user in users],
    )
    logger.debug(
        "Retrieved the users of a school.",
        actor_id=actor_id,
        school=request_data.school,
        user_count=len(users),
        permitted_user_count=sum(1 for user in users if permissions.get(user.id)),
    )
    return UserListData(
        users=users,
        schools=schools,
        school_classes=school_classes,
        work_groups=work_groups,
        permissions=permissions,
    )


async def get_schools(
    schools_get_adapter: SchoolsPersistencePort,
    permissions_port: PermissionsPort,
    users_get_adapter: UsersPersistencePort,
    actor_id: str,
    lang: str,
) -> SchoolsData:
    actor = await get_actor(actor_id, users_get_adapter, lang)
    schools = await schools_get_adapter.get_schools()
    permissions = await permissions_port.get_permissions(
        actor, [school_to_target(school) for school in schools]
    )
    return SchoolsData(schools=_usable_as_filter(schools, permissions, kind="school", actor_id=actor_id))


async def get_school_classes(
    schools_get_adapter: SchoolClassesPersistencePort,
    permissions_port: PermissionsPort,
    users_get_adapter: UsersPersistencePort,
    actor_id: str,
    school_id: str,
    lang: str,
) -> list[SchoolClass]:
    actor = await get_actor(actor_id, users_get_adapter, lang)
    school_classes = await schools_get_adapter.get_school_classes(school_id)
    permissions = await permissions_port.get_permissions(
        actor, [school_class_to_target(school_class) for school_class in school_classes]
    )
    return _usable_as_filter(
        school_classes, permissions, kind="school_class", actor_id=actor_id, school=school_id
    )


async def get_work_groups(
    schools_get_adapter: WorkGroupsPersistencePort,
    permissions_port: PermissionsPort,
    users_get_adapter: UsersPersistencePort,
    actor_id: str,
    school_id: str,
    lang: str,
) -> list[WorkGroup]:
    actor = await get_actor(actor_id, users_get_adapter, lang)
    work_groups = await schools_get_adapter.get_work_groups(school_id)
    permissions = await permissions_port.get_permissions(
        actor, [work_group_to_target(work_group) for work_group in work_groups]
    )
    return _usable_as_filter(
        work_groups, permissions, kind="work_group", actor_id=actor_id, school=school_id
    )


async def _fetch_users(
    users_adapter: UsersPersistencePort,
    target_ids: list[str],
    actor_id: str,
    school: str = "",
) -> tuple[dict[str, User], list[str]]:
    """Fetch the selected users, returning what was found and what was missing.

    With a school, one search covers it; anything it does not answer for is
    fetched by id, which is also the whole job when no school is submitted.
    """
    found: dict[str, User] = {}
    if school:
        wanted = set(target_ids)
        try:
            found = {
                user.id: user
                for user in await users_adapter.get_users(school, [], [])
                if user.id in wanted
            }
        except Exception as exc:
            # The search is only a shortcut; a backend that is really down fails the
            # per-id fetches below too, and those report it.
            logger.warning(
                "Resolving a selection by school failed, falling back to one fetch per user. "
                "Check the Kelvin REST API if this repeats.",
                actor_id=actor_id,
                school=school,
                target_count=len(target_ids),
                error=str(exc),
                error_type=type(exc).__name__,
            )

    remaining = [target_id for target_id in target_ids if target_id not in found]
    logger.debug(
        "Looked up the selected users.",
        actor_id=actor_id,
        school=school,
        from_search=len(found),
        by_id=len(remaining),
    )
    semaphore = asyncio.Semaphore(PASSWORD_RESET_MAX_CONCURRENCY)

    async def _fetch(target_id: str) -> User:
        async with semaphore:
            return await users_adapter.get_user(target_id)

    # return_exceptions=True: without it gather propagates the first exception
    # while the other fetches keep running in the background.
    results = await asyncio.gather(*(_fetch(tid) for tid in remaining), return_exceptions=True)
    missing: list[str] = []
    for target_id, result in zip(remaining, results, strict=False):
        if isinstance(result, ObjectNotFoundError):
            missing.append(target_id)
        elif isinstance(result, BaseException):
            logger.error(
                "Abandoned the password reset: a selected user could not be looked up. "
                "No password was changed. Usually the Kelvin REST API is unreachable or "
                "answered with an error; the reset can be retried once it responds.",
                actor_id=actor_id,
                target_id=target_id,
                target_count=len(target_ids),
                error=str(result),
                error_type=type(result).__name__,
            )
            raise result
        else:
            found[target_id] = result
    if missing:
        logger.warning(
            "Selected users no longer exist, so the list this selection came from predates "
            "their removal. Reloading the list drops them.",
            actor_id=actor_id,
            missing=missing,
            target_count=len(target_ids),
        )
    return found, missing


async def get_password_reset_selection(
    users_adapter: UsersPersistencePort,
    permissions_port: PermissionsPort,
    actor_id: str,
    target_ids: list[str],
    lang: str,
    school: str = "",
) -> PasswordResetSelectionData:
    """Resolve selected user ids into the users the actor may reset.

    Same permission rule and target ceiling as ``set_passwords``, so the dialog
    states a scope the submit would accept.
    """
    deduped_ids = list(dict.fromkeys(target_ids))
    # Resolving costs a round-trip per user, and the submit would refuse this anyway.
    if len(deduped_ids) > PASSWORD_RESET_MAX_TARGETS:
        logger.info(
            "Rejected a password reset: selection exceeds the maximum target count.",
            actor_id=actor_id,
            target_count=len(deduped_ids),
            max_targets=PASSWORD_RESET_MAX_TARGETS,
        )
        return PasswordResetSelectionData(
            users=[], request_error=PasswordResetRequestError.too_many_targets
        )
    actor = await get_actor(actor_id, users_adapter, lang)
    # A vanished user is dropped here; the submit reports it as ``not_found``.
    found, missing = await _fetch_users(users_adapter, deduped_ids, actor_id, school)
    users = list(found.values())

    permissions = await permissions_port.get_permissions(actor, [user_to_target(user) for user in users])
    permitted = [user for user in users if Permission.write_password in permissions.get(user.id, [])]
    denied = len(deduped_ids) - len(permitted)
    logger.debug(
        "Resolved a password reset selection for confirmation.",
        actor_id=actor_id,
        selected=len(deduped_ids),
        resettable=len(permitted),
        denied=denied,
        missing_count=len(missing),
    )
    return PasswordResetSelectionData(
        users=permitted,
        denied=denied,
        supports_change_on_next_login=users_adapter.supports_password_change_on_next_login(),
    )


async def _write_passwords(
    users_adapter: UsersPersistencePort,
    target_ids: list[str],
    password: str,
    actor_id: str,
    change_on_next_login: bool = False,
) -> list[PasswordResetOutcome]:
    semaphore = asyncio.Semaphore(PASSWORD_RESET_MAX_CONCURRENCY)

    async def _write(target_id: str) -> PasswordResetOutcome:
        async with semaphore:
            outcome, reason = PasswordResetOutcomeCode.success, None
            try:
                await users_adapter.set_password(target_id, password, change_on_next_login)
            except ObjectNotFoundError:
                outcome = PasswordResetOutcomeCode.not_found
            except PasswordChangeOnNextLoginUnsupportedError:
                outcome = PasswordResetOutcomeCode.next_login_change_unsupported
            except PasswordResetRejectedError as exc:
                outcome, reason = PasswordResetOutcomeCode.rejected, exc.message
            except Exception:
                # Writes are not atomic: by the time one fails, others have gone
                # through, and escaping the gather would lose the whole report.
                outcome = PasswordResetOutcomeCode.unconfirmed
                logger.exception(
                    "A password reset could not be confirmed, so it is unknown whether this "
                    "user's password changed. Check the account before resetting it again.",
                    actor_id=actor_id,
                    target_id=target_id,
                )
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
    change_on_next_login: bool = False,
    school: str = "",
) -> PasswordResetResultData:
    deduped_ids = list(dict.fromkeys(target_ids))
    logger.debug(
        "Resetting passwords for a selection of users.",
        actor_id=actor_id,
        submitted_count=len(target_ids),
        target_count=len(deduped_ids),
    )
    if not deduped_ids:
        logger.info("Rejected a password reset: no user was selected.", actor_id=actor_id)
        return PasswordResetResultData(outcomes=[], request_error=PasswordResetRequestError.no_targets)
    if len(deduped_ids) > PASSWORD_RESET_MAX_TARGETS:
        logger.info(
            "Rejected a password reset: selection exceeds the maximum target count.",
            actor_id=actor_id,
            target_count=len(deduped_ids),
            max_targets=PASSWORD_RESET_MAX_TARGETS,
        )
        return PasswordResetResultData(
            outcomes=[], request_error=PasswordResetRequestError.too_many_targets
        )
    if not password:
        logger.info(
            "Rejected a password reset: no password was supplied.",
            actor_id=actor_id,
            target_count=len(deduped_ids),
        )
        return PasswordResetResultData(
            outcomes=[], request_error=PasswordResetRequestError.empty_password
        )

    actor = await get_actor(actor_id, users_adapter, lang)
    found, missing = await _fetch_users(users_adapter, deduped_ids, actor_id, school)
    outcomes: dict[str, PasswordResetOutcome] = {
        tid: PasswordResetOutcome(target_id=tid, outcome=PasswordResetOutcomeCode.not_found)
        for tid in missing
    }

    permissions = await permissions_port.get_permissions(
        actor, [user_to_target(user) for user in found.values()]
    )
    permitted_ids = [tid for tid in found if Permission.write_password in permissions.get(tid, [])]
    denied_ids = [tid for tid in found if tid not in permitted_ids]
    for tid in denied_ids:
        logger.info(
            "Denied a password reset: actor lacks write-password on this target.",
            actor_id=actor_id,
            target_id=tid,
        )
        outcomes[tid] = PasswordResetOutcome(
            target_id=tid, outcome=PasswordResetOutcomeCode.permission_denied
        )
    logger.debug(
        "Resolved the password-reset targets.",
        actor_id=actor_id,
        resolved_count=len(found),
        missing_count=len(missing),
        permitted_count=len(permitted_ids),
        denied_count=len(denied_ids),
    )

    for outcome in await _write_passwords(
        users_adapter, permitted_ids, password, actor_id, change_on_next_login
    ):
        outcomes[outcome.target_id] = outcome

    result = PasswordResetResultData(
        outcomes=[outcomes[tid] for tid in deduped_ids],
        selection=PasswordResetSelectionData(
            users=[found[tid] for tid in permitted_ids],
            denied=len(denied_ids),
            supports_change_on_next_login=users_adapter.supports_password_change_on_next_login(),
        ),
    )
    logger.info(
        "Completed a bulk password reset.",
        actor_id=actor_id,
        target_count=len(deduped_ids),
        **Counter(outcome.outcome.value for outcome in result.outcomes),
    )
    return result
