# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import asyncio
from collections import Counter
from collections.abc import Awaitable, Callable
from functools import partial
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
    read: Callable[[], Awaitable[list[_Group]]],
    to_target: Callable[[_Group], Target],
    permissions_port: PermissionsPort,
    actor: User,
    **context: object,
) -> list[_Group]:
    """The groups ``read`` returns that the actor is allowed to filter by, in the order read.

    Takes the read, not its coroutine: a caller cancelled before this starts,
    as a failed listing cancels the group control, would otherwise leave the
    coroutine it already created unawaited.
    """
    fetched = await read()
    permissions = await permissions_port.get_permissions(actor, [to_target(group) for group in fetched])
    return _usable_as_filter(fetched, permissions, actor_id=actor.id, **context)


# The roles the policy lets read every user of a school rather than the users of
# their own groups - see ``school_user_resource.yaml``. Widening this costs a
# school-wide read; narrowing it hides rows the policy allows, so the permission
# filter, not this set, stays the authority on what is shown.
SCHOOL_WIDE_ROLES = frozenset({"school_admin"})


def _sees_whole_school(actor: User, school: str) -> bool:
    return bool(actor.attributes.role_names_in(school) & SCHOOL_WIDE_ROLES)


async def _members_of(
    users_get_adapter: UsersPersistencePort,
    school: str,
    school_classes: list[str],
    work_groups: list[str],
) -> list[User]:
    """The members of the named groups, and none where none are named.

    The port reads the whole school when it is given no group, which is the
    other branch of ``_reachable_users`` - never this one.
    """
    if not (school_classes or work_groups):
        return []
    return await users_get_adapter.get_users(school, school_classes, work_groups)


async def _wards_of(users_get_adapter: UsersPersistencePort, actor: User) -> list[User]:
    """The actor's legal wards, whom no group of the actor's need contain."""
    ward_ids = actor.attributes.legal_wards
    if not ward_ids:
        return []
    found = await users_get_adapter.get_users_by_id(ward_ids)
    return [found[identifier] for identifier in dict.fromkeys(ward_ids) if identifier in found]


async def _may_filter_by(
    permissions_port: PermissionsPort, actor: User, request_data: UsersGetRequest
) -> bool:
    """Whether the actor may filter by every group ``request_data`` names.

    Decided on the id and school the request carries, not on a read of each
    group: the policies look at nothing else, so the check costs one PDP round
    trip and no Kelvin request. A group the school does not have passes it and
    lists nobody, which the caller tells apart from an empty group.
    """
    school = request_data.school
    groups = [(TargetObjectType.SCHOOL_CLASS, group) for group in request_data.school_classes] + [
        (TargetObjectType.WORK_GROUP, group) for group in request_data.work_groups
    ]
    if not groups:
        return True
    permissions = await permissions_port.get_permissions(
        actor,
        [
            Target(
                old_target=TargetObject(id=group, type=kind, attributes={"id": group, "school": school}),
                new_target=None,
            )
            for kind, group in groups
        ],
    )
    refused = [
        group for _, group in groups if Permission.use_as_filter not in permissions.get(group, [])
    ]
    if refused:
        logger.debug(
            "Refused to list a group the actor may not filter by.",
            actor_id=actor.id,
            school=school,
            refused=refused,
        )
    return not refused


async def _reachable_users(
    users_get_adapter: UsersPersistencePort,
    actor: User,
    request_data: UsersGetRequest,
) -> list[User]:
    """The users a listing may show, read from the actor's reach, not the school's size.

    Reading the school returns every user it holds and the permission filter then
    drops all but the few the actor may see - work proportional to the school for
    a result proportional to one teacher's classes, and on a school of a few
    thousand it outruns the Kelvin client's timeout. The actor's own groups, plus
    their wards and themselves, is that same result arrived at by asking for it.

    Deliberately a superset of what the policy grants: it returns every member of
    those groups, where a teacher may read only the students among them. The
    permission filter trims it. A subset would hide rows instead, which is why
    a school-wide role still reads the school.
    """
    if request_data.school_classes or request_data.work_groups:
        return await users_get_adapter.get_users(
            request_data.school, request_data.school_classes, request_data.work_groups
        )
    school = request_data.school
    if _sees_whole_school(actor, school):
        return await users_get_adapter.get_users(school, [], [])
    members, wards = await asyncio.gather(
        _members_of(
            users_get_adapter,
            school,
            actor.attributes.school_classes.get(school, []),
            actor.attributes.work_groups.get(school, []),
        ),
        _wards_of(users_get_adapter, actor),
    )
    listed = {user.id for user in members}
    # The actor belongs to every group of theirs, so they are already here -
    # unless they are in none, and a listing that omits the reader reads as an
    # error. A ward of another school is not part of this school's listing.
    return members + [
        user for user in (actor, *wards) if user.id not in listed and school in user.attributes.schools
    ]


async def get_users(
    users_get_adapter: UsersPersistencePort,
    schools_get_adapter: SchoolsPersistencePort,
    permissions_port: PermissionsPort,
    actor_id: str,
    request_data: UsersGetRequest,
    lang: str,
) -> UserListData | None:
    """The users of ``request_data`` the actor may see, or None for a group they may not name.

    Naming a group makes the service account read every member of it, so a
    hand-edited link must not reach further than a click on the filter control:
    the groups it names have to pass the use-as-filter check that decides which
    groups the control offers.
    """
    actor = await get_actor(actor_id, users_get_adapter, lang)
    if not await _may_filter_by(permissions_port, actor, request_data):
        return None
    users = await _reachable_users(users_get_adapter, actor, request_data)
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
    # A user the actor holds no permission on at all is not listed.
    users = [user for user in users if permissions.get(user.id)]
    return UserListData(
        users=users,
        schools=await schools_get_adapter.get_schools(),
        permissions=permissions,
    )


async def get_schools(
    schools_get_adapter: SchoolsPersistencePort,
    permissions_port: PermissionsPort,
    users_get_adapter: UsersPersistencePort,
    actor_id: str,
    lang: str,
) -> SchoolsData:
    # This is the first thing a page does, so the actor read sat in front of
    # everything else. Only the permission check below needs it, and the school
    # list does not, so the two reads run together and the rest of the request
    # finds the actor already resolved.
    actor, schools = await asyncio.gather(
        get_actor(actor_id, users_get_adapter, lang), schools_get_adapter.get_schools()
    )
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
        partial(schools_get_adapter.get_school_classes, school_id),
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
        partial(schools_get_adapter.get_work_groups, school_id),
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
            partial(school_classes_get_adapter.get_school_classes, school_id),
            school_class_to_target,
            permissions_port,
            actor,
            kind="school_class",
            school=school_id,
        ),
        _filterable(
            partial(work_groups_get_adapter.get_work_groups, school_id),
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
