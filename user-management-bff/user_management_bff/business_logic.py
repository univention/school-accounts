# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import asyncio
from collections import Counter
from collections.abc import Awaitable, Callable
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


_Group = TypeVar("_Group", SchoolClass, WorkGroup)


async def _filterable(
    groups: Awaitable[list[_Group]],
    to_target: Callable[[_Group], Target],
    permissions_port: PermissionsPort,
    actor: User,
    **context: object,
) -> list[_Group]:
    """The groups of ``groups`` the actor is allowed to filter by, in the order read."""
    fetched = await groups
    permissions = await permissions_port.get_permissions(actor, [to_target(group) for group in fetched])
    return _usable_as_filter(fetched, permissions, actor_id=actor.id, **context)


async def _resolve_groups(
    fetch: Callable[[str, list[str]], Awaitable[list[_Group]]],
    needed: dict[str, set[str]],
) -> dict[str, list[_Group]]:
    """Look up the named groups of every school in ``needed``, concurrently."""
    schools = sorted(needed)
    fetched = await asyncio.gather(*(fetch(school, sorted(needed[school])) for school in schools))
    return dict(zip(schools, fetched, strict=False))


async def _fetch_groups(
    school_classes_get_adapter: SchoolClassesPersistencePort,
    work_groups_get_adapter: WorkGroupsPersistencePort,
    users: list[User],
) -> tuple[dict[str, list[SchoolClass]], dict[str, list[WorkGroup]]]:
    """Resolve the group display names the given users' rows will render.

    Asks for exactly the groups those users are in. The whole-school lookup would
    answer the same question in one request per school, but a school can hold
    hundreds of groups, each carrying its full membership - a large, slow response
    almost entirely made of groups nobody is going to render.
    """
    needed_classes: dict[str, set[str]] = {}
    needed_groups: dict[str, set[str]] = {}
    for user in users:
        for school, classes in user.attributes.school_classes.items():
            needed_classes.setdefault(school, set()).update(classes)
        for school, groups in user.attributes.work_groups.items():
            needed_groups.setdefault(school, set()).update(groups)
    # Keyed by school even where the set is empty: the table indexes these by the
    # schools on the user, and a school with no group of one kind still has a row
    # asking for it.
    return await asyncio.gather(
        _resolve_groups(school_classes_get_adapter.get_school_classes_by_name, needed_classes),
        _resolve_groups(work_groups_get_adapter.get_work_groups_by_name, needed_groups),
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
    actor = await get_actor(actor_id, users_get_adapter, lang)
    users = await users_get_adapter.get_users(
        request_data.school, request_data.school_classes, request_data.work_groups
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
    # A user the actor holds no permission on at all is not listed, so their
    # groups are never rendered either. Dropping them before the lookups is what
    # keeps those proportional to what ends up on screen: an unfiltered school
    # listing returns every user of the school, and each one would otherwise pull
    # in the groups of every school they belong to.
    users = [user for user in users if permissions.get(user.id)]
    schools, (school_classes, work_groups) = await asyncio.gather(
        schools_get_adapter.get_schools(),
        _fetch_groups(school_classes_get_adapter, work_groups_get_adapter, users),
    )
    logger.debug(
        "Loaded the group names needed to render the list.",
        schools_scanned=len(school_classes),
        school_class_count=sum(len(items) for items in school_classes.values()),
        work_group_count=sum(len(items) for items in work_groups.values()),
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
    return await _filterable(
        schools_get_adapter.get_school_classes(school_id),
        school_class_to_target,
        permissions_port,
        actor,
        kind="school_class",
        school=school_id,
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
    return await _filterable(
        schools_get_adapter.get_work_groups(school_id),
        work_group_to_target,
        permissions_port,
        actor,
        kind="work_group",
        school=school_id,
    )


async def get_group_filters(
    school_classes_get_adapter: SchoolClassesPersistencePort,
    work_groups_get_adapter: WorkGroupsPersistencePort,
    permissions_port: PermissionsPort,
    users_get_adapter: UsersPersistencePort,
    actor_id: str,
    school_id: str,
    lang: str,
) -> tuple[list[SchoolClass], list[WorkGroup]]:
    """Both filterable datasets of one school, as the group filter control needs them.

    The two are independent whole-school reads, each the slowest call in its own
    right, so running them one after the other made the filter cost their sum.
    Resolving the actor first keeps that one lookup out of the race.
    """
    actor = await get_actor(actor_id, users_get_adapter, lang)
    return await asyncio.gather(
        _filterable(
            school_classes_get_adapter.get_school_classes(school_id),
            school_class_to_target,
            permissions_port,
            actor,
            kind="school_class",
            school=school_id,
        ),
        _filterable(
            work_groups_get_adapter.get_work_groups(school_id),
            work_group_to_target,
            permissions_port,
            actor,
            kind="work_group",
            school=school_id,
        ),
    )


async def _fetch_users(
    users_adapter: UsersPersistencePort, target_ids: list[str], actor_id: str
) -> tuple[dict[str, User], list[str]]:
    """Resolve the selected ids into users, returning what was found and what was missing.

    One search names every id at once, whatever schools they are spread over, so
    the cost of a confirmation no longer grows with the size of the selection.
    """
    try:
        found = await users_adapter.get_users_by_id(target_ids)
    except Exception as exc:
        logger.error(
            "Abandoned the password reset: the selected users could not be looked up. "
            "No password was changed. Usually the Kelvin REST API is unreachable or "
            "answered with an error; the reset can be retried once it responds.",
            actor_id=actor_id,
            target_count=len(target_ids),
            error=str(exc),
            error_type=type(exc).__name__,
        )
        raise
    missing = [target_id for target_id in target_ids if target_id not in found]
    logger.debug(
        "Looked up the selected users.", actor_id=actor_id, found=len(found), missing=len(missing)
    )
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
) -> PasswordResetSelectionData:
    """Resolve selected user ids into the users the actor may reset.

    Same permission rule and target ceiling as ``set_passwords``, so the dialog
    states a scope the submit would accept.
    """
    deduped_ids = list(dict.fromkeys(target_ids))
    # The submit refuses this too, so confirming it would only promise a reset
    # that cannot happen.
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
    found, missing = await _fetch_users(users_adapter, deduped_ids, actor_id)
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
    found, missing = await _fetch_users(users_adapter, deduped_ids, actor_id)
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
