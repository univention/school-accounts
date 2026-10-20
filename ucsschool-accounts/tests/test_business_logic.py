# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Integration tests for the business logic.

These call ``business_logic.*`` directly using the real file-based adapters
obtained from the configured ``ADAPTER_REGISTRY`` (the registry is configured by
the app startup that the session-scoped ``test_client`` fixture triggers).
"""

import asyncio
import re
import sys
from dataclasses import dataclass
from typing import Callable
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

if sys.version_info >= (3, 12):  # pragma: no cover
    from typing import override  # pyright: ignore[reportUnreachable]
else:
    from typing_extensions import override

from ucsschool_accounts import business_logic, presentation
from ucsschool_accounts.adapter_registry import ADAPTER_REGISTRY
from ucsschool_accounts.adapters.permissions import FilePermissionsAdapter
from ucsschool_accounts.adapters.users import FileUsersPersistenceAdapter
from ucsschool_accounts.business_logic import get_schools
from ucsschool_accounts.errors import (
    NoSchoolUserError,
    ObjectNotFoundError,
    PasswordChangeOnNextLoginUnsupportedError,
    PasswordResetRejectedError,
)
from ucsschool_accounts.lang import _
from ucsschool_accounts.models import (
    Permission,
    School,
    Target,
    TargetObjectType,
    User,
    UserAttributes,
    UsersGetRequest,
)
from ucsschool_accounts.ports import (
    PermissionsPort,
    SchoolClassesPersistencePort,
    SchoolsPersistencePort,
    UsersPersistencePort,
    WorkGroupsPersistencePort,
)
from ucsschool_accounts.presentation import PasswordResetOutcomeCode

# The actor id supplied by AlwaysAuthenticatedAdapter in the test environment.
ACTOR_ID = "dev"
TEST_SCHOOL1 = School(id="test_school1", display_name="Test School 1")


@dataclass
class Ports:
    users: UsersPersistencePort
    schools: SchoolsPersistencePort
    school_classes: SchoolClassesPersistencePort
    work_groups: WorkGroupsPersistencePort
    permissions: PermissionsPort


async def _get_ports() -> Ports:
    """Fetch the configured file-based adapters from the registry."""
    return Ports(
        users=await ADAPTER_REGISTRY(UsersPersistencePort),
        schools=await ADAPTER_REGISTRY(SchoolsPersistencePort),
        school_classes=await ADAPTER_REGISTRY(SchoolClassesPersistencePort),
        work_groups=await ADAPTER_REGISTRY(WorkGroupsPersistencePort),
        permissions=await ADAPTER_REGISTRY(PermissionsPort),
    )


@pytest_asyncio.fixture
async def ports(test_client: TestClient) -> Ports:
    # `test_client` triggers app startup, which configures the registry.
    return await _get_ports()


# ---------------------------------------------------------------------------
# Pure helpers / actor resolution
# ---------------------------------------------------------------------------
@pytest.fixture
def users_get_not_found_mock(mocker: MockerFixture) -> AsyncMock:
    users_get_mock = mocker.AsyncMock()
    users_get_mock.get_user.side_effect = ObjectNotFoundError(identifier="USER")
    return users_get_mock


@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["en", "de"])
async def test_get_schools_actor_not_found(
    mocker: MockerFixture, users_get_not_found_mock: AsyncMock, lang: str
):
    user = "USER"
    expected = _("The logged in user '{user}' is not a valid UCS@school user.", lang=lang).format(
        user=user
    )
    schools, permissions = mocker.AsyncMock(), mocker.AsyncMock()
    with pytest.raises(NoSchoolUserError, match=re.escape(expected)) as exc_info:
        await get_schools(schools, permissions, users_get_not_found_mock, "USER", lang)
    assert exc_info.value.identifier == "USER"


# ---------------------------------------------------------------------------
# get_users
# ---------------------------------------------------------------------------
async def _get_users(ports: Ports, school: str, *, lang: str = "en") -> presentation.UserListData:
    result = await business_logic.get_users(
        ports.users,
        ports.schools,
        ports.permissions,
        ACTOR_ID,
        UsersGetRequest(school=school, school_classes=[], work_groups=[]),
        lang,
    )
    # A listing that names no group has no group to refuse.
    assert result is not None
    return result


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "school,expected_ids",
    [
        ("NON_EXISTENT", set()),
        ("test_school1", {"test_user1", "test_user4"}),
        ("test_school2", {"test_user2", "test_user3"}),
    ],
)
async def test_get_users(ports: Ports, school: str, expected_ids: set[str]):
    result = await _get_users(ports, school)
    assert {user.id for user in result.users} == expected_ids


@pytest.mark.asyncio
async def test_get_users_reads_no_groups(ports: Ports, mocker: MockerFixture):
    """The table shows no classes or work groups, so listing users costs no group read."""
    spies = [
        mocker.spy(ports.school_classes, "get_school_classes"),
        mocker.spy(ports.work_groups, "get_work_groups"),
        mocker.spy(ports.school_classes, "get_school_classes_by_name"),
        mocker.spy(ports.work_groups, "get_work_groups_by_name"),
    ]
    await _get_users(ports, "test_school2")
    for spy in spies:
        spy.assert_not_called()


@pytest.mark.asyncio
@patch.object(
    FilePermissionsAdapter,
    "get_permissions",
    return_value={"test_user2": [Permission.read_last_name]},
)
async def test_get_users_drops_users_the_actor_cannot_see(_permissions_mock: MagicMock, ports: Ports):
    result = await _get_users(ports, "test_school2")
    assert [user.id for user in result.users] == ["test_user2"]


@pytest.mark.asyncio
@patch.object(FilePermissionsAdapter, "get_permissions", return_value={})
async def test_get_users_no_permissions(_permissions_mock: MagicMock, ports: Ports):
    # Users for whom the actor holds no permissions are omitted from the view.
    result = await _get_users(ports, "test_school1")
    assert presentation.build_user_list(result, "en", TEST_SCHOOL1).rows == []


@pytest.mark.asyncio
async def test_get_users_lists_a_group_the_actor_may_filter_by(ports: Ports, mocker: MockerFixture):
    get_permissions_spy = mocker.spy(ports.permissions, "get_permissions")

    result = await business_logic.get_users(
        ports.users,
        ports.schools,
        ports.permissions,
        ACTOR_ID,
        UsersGetRequest(school="test_school1", school_classes=["1a"], work_groups=[]),
        "en",
    )

    assert result is not None
    # The policy decides on the id and school alone, so the group is not read for it.
    group_target = get_permissions_spy.call_args_list[0].args[1][0].old_target
    assert (group_target.id, group_target.type, group_target.attributes) == (
        "1a",
        TargetObjectType.SCHOOL_CLASS,
        {"id": "1a", "school": "test_school1"},
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("school_classes,work_groups", [(["2b"], []), ([], ["w1a"]), (["1a"], ["w1a"])])
async def test_get_users_refuses_a_group_the_actor_may_not_filter_by(
    ports: Ports, mocker: MockerFixture, school_classes: list[str], work_groups: list[str]
):
    """Naming a group makes the service account read all of its members, so every
    group named has to pass - one the actor may use does not carry another."""
    mocker.patch.object(
        ports.permissions,
        "get_permissions",
        mocker.AsyncMock(
            return_value={"1a": [Permission.use_as_filter], "2b": [Permission.read_last_name]}
        ),
    )
    get_users_spy = mocker.spy(ports.users, "get_users")

    result = await business_logic.get_users(
        ports.users,
        ports.schools,
        ports.permissions,
        ACTOR_ID,
        UsersGetRequest(school="test_school1", school_classes=school_classes, work_groups=work_groups),
        "en",
    )

    assert result is None
    get_users_spy.assert_not_called()


async def _get_users_from(ports: Ports, school: str) -> presentation.UserListData:
    result = await business_logic.get_users(
        ports.users,
        ports.schools,
        ports.permissions,
        ACTOR_ID,
        UsersGetRequest(school=school, school_classes=[], work_groups=[]),
        "en",
    )
    # A listing that names no group has no group to refuse.
    assert result is not None
    return result


def _person(
    identifier: str,
    *,
    roles: list[str],
    schools: list[str],
    school_classes: dict[str, list[str]] | None = None,
    work_groups: dict[str, list[str]] | None = None,
    legal_wards: list[str] | None = None,
) -> User:
    return User(
        id=identifier,
        attributes=UserAttributes(
            last_name="L",
            first_name="F",
            username=identifier,
            disabled=False,
            schools=schools,
            school_classes=school_classes or {},
            work_groups=work_groups or {},
            roles=roles,
            legal_wards=legal_wards or [],
        ),
    )


@dataclass
class _Mocked:
    """The ports, and the one mock the assertions are about."""

    ports: Ports
    users: AsyncMock


def _mocked_ports(
    mocker: MockerFixture,
    actor: User,
    *,
    members: list[User],
    by_id: dict[str, User] | None = None,
    granted: tuple[Permission, ...] = (Permission.read_last_name,),
) -> _Mocked:
    """Ports that answer, so the assertions can be about which reads happened."""

    def _granted(_actor: User, targets: list[Target]) -> dict[str, list[Permission]]:
        return {target.old_target.id: list(granted) for target in targets if target.old_target}

    users = mocker.AsyncMock()
    users.get_user.return_value = actor
    users.get_users.return_value = members
    users.get_users_by_id.return_value = by_id or {}
    permissions = mocker.AsyncMock()
    permissions.get_permissions.side_effect = _granted
    schools = mocker.AsyncMock()
    schools.get_schools.return_value = []
    school_classes = mocker.AsyncMock()
    school_classes.get_school_classes_by_name.return_value = []
    work_groups = mocker.AsyncMock()
    work_groups.get_work_groups_by_name.return_value = []
    return _Mocked(
        ports=Ports(
            users=users,
            schools=schools,
            school_classes=school_classes,
            work_groups=work_groups,
            permissions=permissions,
        ),
        users=users,
    )


@pytest.mark.asyncio
async def test_get_users_reads_the_actors_groups_not_the_school(mocker: MockerFixture):
    """Reading the school and letting the permission filter discard it is work
    proportional to the school for a result proportional to one teacher's classes."""
    actor = _person(
        "teach",
        roles=["teacher:school:school1"],
        schools=["school1"],
        school_classes={"school1": ["1a"]},
        work_groups={"school1": ["w1"]},
    )
    pupil = _person("pupil", roles=["student:school:school1"], schools=["school1"])
    mocked = _mocked_ports(mocker, actor, members=[actor, pupil])

    result = await _get_users_from(mocked.ports, "school1")

    assert [user.id for user in result.users] == ["teach", "pupil"]
    mocked.users.get_users.assert_awaited_once_with("school1", ["1a"], ["w1"])


@pytest.mark.asyncio
async def test_get_users_of_a_school_wide_role_still_reads_the_school(mocker: MockerFixture):
    """The policy lets a school admin read every user of their school, so narrowing
    the read to their own classes would hide rows they are allowed to see."""
    actor = _person(
        "admin",
        roles=["school_admin:school:school1"],
        schools=["school1"],
        school_classes={"school1": ["1a"]},
    )
    mocked = _mocked_ports(mocker, actor, members=[])

    await _get_users_from(mocked.ports, "school1")

    mocked.users.get_users.assert_awaited_once_with("school1", [], [])


@pytest.mark.asyncio
async def test_get_users_lists_the_actors_wards(mocker: MockerFixture):
    """A guardian may read their ward whatever group the ward is in, so a listing
    built from the actor's own groups has to add them back."""
    actor = _person(
        "parent",
        roles=["teacher:school:school1"],
        schools=["school1"],
        school_classes={"school1": ["1a"]},
        legal_wards=["ward", "ward", "elsewhere", "gone"],
    )
    ward = _person("ward", roles=["student:school:school1"], schools=["school1"])
    elsewhere = _person("elsewhere", roles=["student:school:school2"], schools=["school2"])
    mocked = _mocked_ports(mocker, actor, members=[actor], by_id={"ward": ward, "elsewhere": elsewhere})

    result = await _get_users_from(mocked.ports, "school1")

    # Named twice but listed once, a ward of another school is not part of this
    # school's listing, and one that no longer exists is simply absent.
    assert [user.id for user in result.users] == ["parent", "ward"]
    mocked.users.get_users_by_id.assert_awaited_once_with(["ward", "ward", "elsewhere", "gone"])


@pytest.mark.asyncio
async def test_get_users_lists_the_actor_who_is_in_no_group(mocker: MockerFixture):
    """A listing that omits its own reader reads as an empty school rather than as
    what it is, and the port would read the whole school if asked for no group."""
    actor = _person("staffer", roles=["staff:school:school1"], schools=["school1"])
    mocked = _mocked_ports(mocker, actor, members=[])

    result = await _get_users_from(mocked.ports, "school1")

    assert [user.id for user in result.users] == ["staffer"]
    mocked.users.get_users.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_users_of_a_school_the_actor_has_nothing_in_lists_nobody(mocker: MockerFixture):
    """A deep link can name any school; one the actor does not reach is empty, not
    the whole school."""
    actor = _person(
        "teach",
        roles=["teacher:school:school1"],
        schools=["school1"],
        school_classes={"school1": ["1a"]},
    )
    mocked = _mocked_ports(mocker, actor, members=[])

    result = await _get_users_from(mocked.ports, "school2")

    assert result.users == []
    mocked.users.get_users.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "school,school_class,role,expected_ids",
    [
        ("test_school1", "", "", {"test_user1", "test_user4"}),
        ("test_school1", "", "school_admin", {"test_user4"}),
        ("test_school1", "1a", "teacher", {"test_user1"}),
        ("test_school2", "", "teacher", {"test_user2", "test_user3"}),
        # test_user3 is a student only at test_school3.
        ("test_school2", "", "student", set[str]()),
    ],
)
async def test_get_users_lists_only_the_selected_role_at_the_school(
    ports: Ports, school: str, school_class: str, role: str, expected_ids: set[str]
):
    school_classes = [school_class] if school_class else []
    result = await business_logic.get_users(
        ports.users,
        ports.schools,
        ports.permissions,
        ACTOR_ID,
        UsersGetRequest(school=school, school_classes=school_classes, work_groups=[], role=role),
        "en",
    )
    assert result is not None
    assert {user.id for user in result.users} == expected_ids


@pytest.mark.asyncio
async def test_get_users_filters_the_actors_reach_and_wards_by_role(mocker: MockerFixture):
    actor = _person(
        "teach",
        roles=["teacher:school:school1"],
        schools=["school1"],
        school_classes={"school1": ["1a"]},
        legal_wards=["ward", "kid"],
    )
    pupil = _person("pupil", roles=["student:school:school1"], schools=["school1"])
    ward = _person("ward", roles=["student:school:school1"], schools=["school1"])
    kid = _person("kid", roles=["staff:school:school1"], schools=["school1"])
    mocked = _mocked_ports(
        mocker,
        actor,
        members=[actor, pupil],
        by_id={"ward": ward, "kid": kid},
        granted=(Permission.read_roles,),
    )

    result = await business_logic.get_users(
        mocked.ports.users,
        mocked.ports.schools,
        mocked.ports.permissions,
        "teach",
        UsersGetRequest(school="school1", school_classes=[], work_groups=[], role="student"),
        "en",
    )

    assert result is not None
    assert [user.id for user in result.users] == ["pupil", "ward"]


@pytest.mark.asyncio
async def test_get_users_by_role_drops_users_whose_roles_the_actor_cannot_read(mocker: MockerFixture):
    """Listing a user under a role would reveal the role the table hides."""
    actor = _person("admin", roles=["school_admin:school:school1"], schools=["school1"])
    pupil = _person("pupil", roles=["student:school:school1"], schools=["school1"])
    mocked = _mocked_ports(mocker, actor, members=[pupil])

    result = await business_logic.get_users(
        mocked.ports.users,
        mocked.ports.schools,
        mocked.ports.permissions,
        "admin",
        UsersGetRequest(school="school1", school_classes=[], work_groups=[], role="student"),
        "en",
    )

    assert result is not None
    assert result.users == []


# ---------------------------------------------------------------------------
# get_schools / get_school_classes / get_work_groups
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_schools(ports: Ports):
    result = await business_logic.get_schools(
        ports.schools, ports.permissions, ports.users, ACTOR_ID, "en"
    )
    assert [school.id for school in result.schools] == [
        "school1",
        "school2",
        "school3",
        "school4",
        "test_school1",
        "test_school2",
        "test_school3",
    ]


@pytest.mark.asyncio
async def test_get_school_classes(ports: Ports):
    result = await business_logic.get_school_classes(
        ports.school_classes,
        ports.permissions,
        ports.users,
        ACTOR_ID,
        "school1",
        "en",
    )
    assert [(sc.id, sc.display_name) for sc in result] == [("1a", "1a"), ("2b", "2b")]


@pytest.mark.asyncio
async def test_get_work_groups(ports: Ports):
    result = await business_logic.get_work_groups(
        ports.work_groups,
        ports.permissions,
        ports.users,
        ACTOR_ID,
        "school1",
        "en",
    )
    assert [(wg.id, wg.display_name) for wg in result] == [("w1a", "w1a"), ("w2b", "w2b")]


# ---------------------------------------------------------------------------
# Edge cases / branch behaviour beyond plain line coverage
#
# The file permissions adapter grants permissions per target *type*, so the
# integration tests above cannot exercise per-object permission differences.
# These tests mock get_permissions to return per-id results.
# ---------------------------------------------------------------------------
def _permissions_by_id(mapping: dict[str, list[Permission]]):
    """Build a get_permissions side effect returning ``mapping`` keyed by target id.

    Any target not present in ``mapping`` resolves to an empty permission list.
    """

    def _target_id(target: Target) -> str:
        target_object = target.old_target or target.new_target
        # Every target built by business_logic.*_to_target sets old_target (or both).
        assert target_object is not None
        return target_object.id

    def _side_effect(actor: User, targets: list[Target]):
        return {(target_id := _target_id(target)): mapping.get(target_id, []) for target in targets}

    return _side_effect


# get_schools / get_school_classes / get_work_groups filter out entries the actor
# may not use as a filter (the False side of the use_as_filter check).
@pytest.mark.asyncio
async def test_get_schools_filters_by_use_as_filter(ports: Ports, mocker: MockerFixture):
    mocker.patch.object(
        FilePermissionsAdapter,
        "get_permissions",
        side_effect=_permissions_by_id({"school1": [Permission.use_as_filter]}),
    )
    result = await business_logic.get_schools(
        ports.schools, ports.permissions, ports.users, ACTOR_ID, "en"
    )
    # Every other school is dropped because the actor lacks use_as_filter on it.
    assert [school.id for school in result.schools] == ["school1"]


@pytest.mark.asyncio
async def test_get_school_classes_filters_by_use_as_filter(ports: Ports, mocker: MockerFixture):
    mocker.patch.object(
        FilePermissionsAdapter,
        "get_permissions",
        side_effect=_permissions_by_id({"1a": [Permission.use_as_filter]}),
    )
    result = await business_logic.get_school_classes(
        ports.school_classes,
        ports.permissions,
        ports.users,
        ACTOR_ID,
        "school1",
        "en",
    )
    # "2b" is dropped because the actor lacks use_as_filter on it.
    assert [sc.id for sc in result] == ["1a"]


@pytest.mark.asyncio
async def test_get_work_groups_filters_by_use_as_filter(ports: Ports, mocker: MockerFixture):
    mocker.patch.object(
        FilePermissionsAdapter,
        "get_permissions",
        side_effect=_permissions_by_id({"w1a": [Permission.use_as_filter]}),
    )
    result = await business_logic.get_work_groups(
        ports.work_groups,
        ports.permissions,
        ports.users,
        ACTOR_ID,
        "school1",
        "en",
    )
    assert [wg.id for wg in result] == ["w1a"]


# get_users returns only the users the actor holds a permission for
# (partial visibility, not the all-or-nothing cases above).
@pytest.mark.asyncio
async def test_get_users_partial_visibility(ports: Ports, mocker: MockerFixture):
    mocker.patch.object(
        FilePermissionsAdapter,
        "get_permissions",
        side_effect=_permissions_by_id({"test_user1": [Permission.read_first_name]}),
    )
    result = await _get_users(ports, "test_school1")
    # test_school1 also contains test_user4, but the actor has no permission for it,
    # so only test_user1 is rendered into a row.
    view = presentation.build_user_list(result, "en", TEST_SCHOOL1)
    # The username cell is the third column and is always readable.
    assert [row.cells[2].text for row in view.rows] == ["firstname.lastname"]


# ---------------------------------------------------------------------------
# set_passwords
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_set_passwords_carries_the_selection_it_resolved(
    ports: Ports,
    mocker: MockerFixture,
    patch_set_password: Callable[[dict[str, Exception]], MagicMock],
):
    """The dialog is re-rendered from this when a password is refused."""
    patch_set_password({})
    result = await business_logic.set_passwords(
        ports.users, ports.permissions, ACTOR_ID, ["test_user1"], "new-password", "en"
    )
    assert result.selection is not None
    assert [user.id for user in result.selection.users] == ["test_user1"]


@pytest.mark.asyncio
async def test_set_passwords_success(
    ports: Ports,
    mocker: MockerFixture,
    patch_set_password: Callable[[dict[str, Exception]], MagicMock],
):
    patch_set_password({})
    mocker.patch.object(
        FilePermissionsAdapter,
        "get_permissions",
        side_effect=_permissions_by_id(
            {"test_user1": [Permission.write_password], "test_user2": [Permission.write_password]}
        ),
    )
    result = await business_logic.set_passwords(
        ports.users, ports.permissions, ACTOR_ID, ["test_user1", "test_user2"], "new-password", "en"
    )
    assert {outcome.target_id: outcome.outcome for outcome in result.outcomes} == {
        "test_user1": PasswordResetOutcomeCode.success,
        "test_user2": PasswordResetOutcomeCode.success,
    }


@pytest.mark.asyncio
async def test_set_passwords_denies_permission_per_user_without_aborting_others(
    ports: Ports,
    mocker: MockerFixture,
    patch_set_password: Callable[[dict[str, Exception]], MagicMock],
):
    set_password_mock = patch_set_password({})
    mocker.patch.object(
        FilePermissionsAdapter,
        "get_permissions",
        side_effect=_permissions_by_id({"test_user1": [Permission.write_password]}),
    )
    result = await business_logic.set_passwords(
        ports.users, ports.permissions, ACTOR_ID, ["test_user1", "test_user2"], "new-password", "en"
    )
    assert {outcome.target_id: outcome.outcome for outcome in result.outcomes} == {
        "test_user1": PasswordResetOutcomeCode.success,
        "test_user2": PasswordResetOutcomeCode.permission_denied,
    }
    set_password_mock.assert_awaited_once_with("test_user1", "new-password", False)


@pytest.mark.asyncio
async def test_set_passwords_actor_can_include_self(
    ports: Ports,
    mocker: MockerFixture,
    patch_set_password: Callable[[dict[str, Exception]], MagicMock],
):
    patch_set_password({})
    mocker.patch.object(
        FilePermissionsAdapter,
        "get_permissions",
        side_effect=_permissions_by_id(
            {ACTOR_ID: [Permission.write_password], "test_user1": [Permission.write_password]}
        ),
    )
    result = await business_logic.set_passwords(
        ports.users, ports.permissions, ACTOR_ID, [ACTOR_ID, "test_user1"], "new-password", "en"
    )
    assert {outcome.target_id: outcome.outcome for outcome in result.outcomes} == {
        ACTOR_ID: PasswordResetOutcomeCode.success,
        "test_user1": PasswordResetOutcomeCode.success,
    }


@pytest.mark.asyncio
async def test_set_passwords_partial_failure_returns_per_user_outcomes(
    ports: Ports,
    mocker: MockerFixture,
    patch_set_password: Callable[[dict[str, Exception]], MagicMock],
):
    target_ids = ["test_user1", "test_user2", "test_user3"]
    mocker.patch.object(
        FilePermissionsAdapter,
        "get_permissions",
        side_effect=_permissions_by_id({tid: [Permission.write_password] for tid in target_ids}),
    )

    set_password_mock = patch_set_password(
        {
            "test_user2": ObjectNotFoundError(identifier="test_user2"),
            "test_user3": PasswordResetRejectedError(
                identifier="test_user3", message="policy violation"
            ),
        }
    )
    result = await business_logic.set_passwords(
        ports.users, ports.permissions, ACTOR_ID, target_ids, "new-password", "en"
    )
    outcomes_by_id = {outcome.target_id: outcome for outcome in result.outcomes}
    assert outcomes_by_id["test_user1"].outcome == PasswordResetOutcomeCode.success
    assert outcomes_by_id["test_user2"].outcome == PasswordResetOutcomeCode.not_found
    assert outcomes_by_id["test_user3"].outcome == PasswordResetOutcomeCode.rejected
    assert outcomes_by_id["test_user3"].reason == "policy violation"
    assert set_password_mock.await_count == 3


@pytest.mark.asyncio
async def test_set_passwords_leaves_a_user_alone_whose_next_login_flag_cannot_be_set(
    ports: Ports, patch_set_password: Callable[[dict[str, Exception]], MagicMock]
):
    """The actor asked for both; a password without the flag is not what they asked for."""
    patch_set_password(
        {"test_user2": PasswordChangeOnNextLoginUnsupportedError(identifier="test_user2")}
    )
    result = await business_logic.set_passwords(
        ports.users,
        ports.permissions,
        ACTOR_ID,
        ["test_user1", "test_user2"],
        "new-password",
        "en",
        change_on_next_login=True,
    )
    by_id = {outcome.target_id: outcome.outcome for outcome in result.outcomes}
    assert by_id["test_user1"] == PasswordResetOutcomeCode.success
    assert by_id["test_user2"] == PasswordResetOutcomeCode.next_login_change_unsupported


@pytest.mark.asyncio
async def test_set_passwords_missing_target_returns_not_found_outcome_without_aborting_others(
    ports: Ports,
    mocker: MockerFixture,
    patch_set_password: Callable[[dict[str, Exception]], MagicMock],
):
    set_password_mock = patch_set_password({})
    mocker.patch.object(
        FilePermissionsAdapter,
        "get_permissions",
        side_effect=_permissions_by_id({"test_user1": [Permission.write_password]}),
    )
    result = await business_logic.set_passwords(
        ports.users,
        ports.permissions,
        ACTOR_ID,
        ["test_user1", "NON_EXISTENT"],
        "new-password",
        "en",
    )
    assert [outcome.outcome for outcome in result.outcomes] == [
        PasswordResetOutcomeCode.success,
        PasswordResetOutcomeCode.not_found,
    ]
    set_password_mock.assert_awaited_once_with("test_user1", "new-password", False)


@pytest.mark.asyncio
async def test_set_passwords_unexpected_fetch_error_still_aborts_whole_request(
    ports: Ports,
    mocker: MockerFixture,
    patch_set_password: Callable[[dict[str, Exception]], MagicMock],
):
    set_password_mock = patch_set_password({})
    mocker.patch.object(
        FileUsersPersistenceAdapter,
        "get_users_by_id",
        side_effect=RuntimeError("Kelvin is unreachable"),
    )
    with pytest.raises(RuntimeError, match="Kelvin is unreachable"):
        await business_logic.set_passwords(
            ports.users, ports.permissions, ACTOR_ID, ["test_user1", "test_user2"], "new-password", "en"
        )
    set_password_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_set_passwords_preserves_request_order_across_outcome_kinds(
    ports: Ports,
    mocker: MockerFixture,
    patch_set_password: Callable[[dict[str, Exception]], MagicMock],
):
    mocker.patch.object(
        FilePermissionsAdapter,
        "get_permissions",
        side_effect=_permissions_by_id({"test_user1": [Permission.write_password]}),
    )
    patch_set_password({})
    result = await business_logic.set_passwords(
        ports.users,
        ports.permissions,
        ACTOR_ID,
        ["NON_EXISTENT", "test_user2", "test_user1"],
        "new-password",
        "en",
    )
    assert [outcome.target_id for outcome in result.outcomes] == [
        "NON_EXISTENT",
        "test_user2",
        "test_user1",
    ]
    assert [outcome.outcome for outcome in result.outcomes] == [
        PasswordResetOutcomeCode.not_found,
        PasswordResetOutcomeCode.permission_denied,
        PasswordResetOutcomeCode.success,
    ]


@pytest.mark.asyncio
async def test_set_passwords_deduplicates_target_ids(
    ports: Ports,
    mocker: MockerFixture,
    patch_set_password: Callable[[dict[str, Exception]], MagicMock],
):
    mocker.patch.object(
        FilePermissionsAdapter,
        "get_permissions",
        side_effect=_permissions_by_id({"test_user1": [Permission.write_password]}),
    )
    set_password_mock = patch_set_password({})
    result = await business_logic.set_passwords(
        ports.users, ports.permissions, ACTOR_ID, ["test_user1", "test_user1"], "new-password", "en"
    )
    assert [outcome.target_id for outcome in result.outcomes] == ["test_user1"]
    set_password_mock.assert_awaited_once_with("test_user1", "new-password", False)


@pytest.mark.asyncio
async def test_set_passwords_empty_target_ids_returns_no_outcomes(ports: Ports, mocker: MockerFixture):
    get_permissions_mock = mocker.patch.object(FilePermissionsAdapter, "get_permissions")
    get_user_mock = mocker.patch.object(FileUsersPersistenceAdapter, "get_user")
    result = await business_logic.set_passwords(
        ports.users, ports.permissions, ACTOR_ID, [], "new-password", "en"
    )
    assert result.outcomes == []
    assert result.request_error == presentation.PasswordResetRequestError.no_targets
    get_permissions_mock.assert_not_called()
    get_user_mock.assert_not_called()


@pytest.mark.asyncio
async def test_set_passwords_empty_password_is_rejected_without_any_writes(
    ports: Ports,
    mocker: MockerFixture,
    patch_set_password: Callable[[dict[str, Exception]], MagicMock],
):
    get_permissions_mock = mocker.patch.object(FilePermissionsAdapter, "get_permissions")
    get_user_mock = mocker.patch.object(FileUsersPersistenceAdapter, "get_user")
    set_password_mock = patch_set_password({})
    result = await business_logic.set_passwords(
        ports.users, ports.permissions, ACTOR_ID, ["test_user1"], "", "en"
    )
    assert result.outcomes == []
    assert result.request_error == presentation.PasswordResetRequestError.empty_password
    get_permissions_mock.assert_not_called()
    get_user_mock.assert_not_called()
    set_password_mock.assert_not_called()


@pytest.mark.asyncio
async def test_a_selection_is_resolved_by_one_search(ports: Ports, mocker: MockerFixture):
    """One request per selected user is what the proxy could not take. A selection
    outlives a filter change, so it can span schools - the search names them all
    anyway, and costs the same one round-trip."""
    get_users_by_id_spy = mocker.spy(FileUsersPersistenceAdapter, "get_users_by_id")
    get_user_spy = mocker.spy(FileUsersPersistenceAdapter, "get_user")
    data = await business_logic.get_password_reset_selection(
        ports.users, ports.permissions, ACTOR_ID, ["test_user1", "test_user2", "test_user4"], "en"
    )
    assert {user.id for user in data.users} == {"test_user1", "test_user2", "test_user4"}
    assert get_users_by_id_spy.call_count == 1
    # Only the actor, never the targets.
    assert get_user_spy.call_count == 1


@pytest.mark.asyncio
async def test_get_password_reset_selection_too_many_targets_is_rejected_without_any_reads(
    ports: Ports, mocker: MockerFixture
):
    """The submit refuses this too, so confirming it would promise a reset that cannot happen."""
    get_permissions_mock = mocker.patch.object(FilePermissionsAdapter, "get_permissions")
    get_user_mock = mocker.patch.object(FileUsersPersistenceAdapter, "get_user")
    mocker.patch.object(business_logic, "PASSWORD_RESET_MAX_TARGETS", 2)
    data = await business_logic.get_password_reset_selection(
        ports.users,
        ports.permissions,
        ACTOR_ID,
        ["test_user1", "test_user2", "test_user3"],
        "en",
    )
    assert data.users == []
    assert data.request_error == presentation.PasswordResetRequestError.too_many_targets
    get_user_mock.assert_not_called()
    get_permissions_mock.assert_not_called()


@pytest.mark.asyncio
async def test_get_password_reset_selection_counts_duplicates_once(ports: Ports, mocker: MockerFixture):
    """The ceiling applies to the deduplicated ids, as it does on submit."""
    mocker.patch.object(business_logic, "PASSWORD_RESET_MAX_TARGETS", 2)
    data = await business_logic.get_password_reset_selection(
        ports.users,
        ports.permissions,
        ACTOR_ID,
        ["test_user1", "test_user1", "test_user2"],
        "en",
    )
    assert data.request_error is None
    assert [user.id for user in data.users] == ["test_user1", "test_user2"]


@pytest.mark.asyncio
async def test_a_write_that_times_out_does_not_discard_the_other_outcomes(
    ports: Ports, patch_set_password: Callable[[dict[str, Exception]], MagicMock]
):
    """Writes are not atomic. Letting the failure escape the gather returned a 500 and
    left nobody able to say which passwords had already been changed."""
    patch_set_password({"test_user2": httpx.ReadTimeout("timed out")})
    result = await business_logic.set_passwords(
        ports.users,
        ports.permissions,
        ACTOR_ID,
        ["test_user1", "test_user2"],
        "new-password",
        "en",
    )
    by_id = {outcome.target_id: outcome.outcome for outcome in result.outcomes}
    assert by_id["test_user1"] == presentation.PasswordResetOutcomeCode.success
    assert by_id["test_user2"] == presentation.PasswordResetOutcomeCode.unconfirmed


@pytest.mark.asyncio
async def test_set_passwords_too_many_targets_is_rejected_without_any_writes(
    ports: Ports,
    mocker: MockerFixture,
    patch_set_password: Callable[[dict[str, Exception]], MagicMock],
):
    get_permissions_mock = mocker.patch.object(FilePermissionsAdapter, "get_permissions")
    get_user_mock = mocker.patch.object(FileUsersPersistenceAdapter, "get_user")
    set_password_mock = patch_set_password({})
    mocker.patch.object(business_logic, "PASSWORD_RESET_MAX_TARGETS", 2)
    result = await business_logic.set_passwords(
        ports.users,
        ports.permissions,
        ACTOR_ID,
        ["test_user1", "test_user2", "test_user3"],
        "new-password",
        "en",
    )
    assert result.outcomes == []
    assert result.request_error == presentation.PasswordResetRequestError.too_many_targets
    get_permissions_mock.assert_not_called()
    get_user_mock.assert_not_called()
    set_password_mock.assert_not_called()


@pytest.mark.asyncio
async def test_set_passwords_bounds_concurrency(mocker: MockerFixture):
    class _ConcurrencyTrackingUsersAdapter(UsersPersistencePort):
        def __init__(self) -> None:
            self.current: int = 0
            self.high_water_mark: int = 0

        @override
        async def get_users(
            self, school: str, school_classes: list[str], work_groups: list[str]
        ) -> list[User]:
            raise NotImplementedError

        @override
        async def get_user(self, identifier: str) -> User:
            return User(
                id=identifier,
                attributes=UserAttributes(
                    last_name="L",
                    first_name="F",
                    username=identifier,
                    disabled=False,
                    schools=[],
                    school_classes={},
                    work_groups={},
                    roles=[],
                ),
            )

        @override
        async def get_users_by_id(self, identifiers: list[str]) -> dict[str, User]:
            return {identifier: await self.get_user(identifier) for identifier in identifiers}

        @override
        def supports_password_change_on_next_login(self) -> bool:
            return True

        @override
        async def set_password(
            self, identifier: str, password: str, change_on_next_login: bool = False
        ) -> None:
            self.current += 1
            self.high_water_mark = max(self.high_water_mark, self.current)
            await asyncio.sleep(0)
            self.current -= 1

    users_adapter = _ConcurrencyTrackingUsersAdapter()
    target_ids = [f"target-{i}" for i in range(10)]
    permissions_mock = mocker.MagicMock(spec=PermissionsPort)
    permissions_mock.get_permissions.side_effect = _permissions_by_id(
        {tid: [Permission.write_password] for tid in target_ids}
    )
    mocker.patch.object(business_logic, "PASSWORD_RESET_MAX_CONCURRENCY", 3)
    await business_logic.set_passwords(
        users_adapter, permissions_mock, ACTOR_ID, target_ids, "new-password", "en"
    )
    assert users_adapter.high_water_mark <= 3
    assert users_adapter.high_water_mark > 1


# ---------------------------------------------------------------------------
# get_password_reset_selection - what the confirmation dialog states
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("target_ids", "expected_denied"),
    [
        # Only test_user1 is resettable, so the second id is dropped either way -
        # what differs is whether dropping it counts against the actor.
        pytest.param(["test_user1", "test_user2"], 1, id="denied-by-permission"),
        pytest.param(["test_user1", "nonexistent"], 1, id="denied-by-not-existing"),
        pytest.param(["test_user1", "test_user1"], 0, id="a-duplicate-is-not-a-denial"),
    ],
)
async def test_password_reset_selection_keeps_only_resettable_users(
    ports: Ports, mocker: MockerFixture, target_ids: list[str], expected_denied: int
):
    mocker.patch.object(
        FilePermissionsAdapter,
        "get_permissions",
        side_effect=_permissions_by_id({"test_user1": [Permission.write_password]}),
    )
    data = await business_logic.get_password_reset_selection(
        ports.users, ports.permissions, ACTOR_ID, target_ids, "en"
    )
    assert [user.id for user in data.users] == ["test_user1"]
    assert data.denied == expected_denied


@pytest.mark.asyncio
async def test_password_reset_selection_propagates_an_unexpected_fetch_error(
    ports: Ports, mocker: MockerFixture
):
    """A missing user is an anticipated outcome; anything else is systemic."""
    # get_user is left alone, so the failure comes from resolving the selection
    # rather than from get_actor.
    mocker.patch.object(
        FileUsersPersistenceAdapter, "get_users_by_id", side_effect=RuntimeError("kelvin is down")
    )
    with pytest.raises(RuntimeError, match="kelvin is down"):
        await business_logic.get_password_reset_selection(
            ports.users, ports.permissions, ACTOR_ID, ["test_user1"], "en"
        )


@pytest.mark.asyncio
async def test_get_group_filters_reads_both_kinds_and_the_actor_once(
    ports: Ports, mocker: MockerFixture
):
    get_user_spy = mocker.spy(FileUsersPersistenceAdapter, "get_user")

    school_classes, work_groups = await business_logic.get_group_filters(
        ports.school_classes,
        ports.work_groups,
        ports.permissions,
        ports.users,
        ACTOR_ID,
        "school1",
        "en",
    )

    assert [school_class.id for school_class in school_classes] == ["1a", "2b"]
    assert [work_group.id for work_group in work_groups] == ["w1a", "w2b"]
    # Resolving it per kind would put the actor lookup back into the race the two
    # whole-school reads now run in.
    assert get_user_spy.call_count == 1


@pytest.mark.asyncio
async def test_a_cancelled_group_filter_read_leaves_no_read_behind(mocker: MockerFixture):
    """A failed listing cancels the group control before its reads run. A read
    created up front would then be a coroutine nobody awaits."""
    school_classes = mocker.AsyncMock()
    work_groups = mocker.AsyncMock()
    mocker.patch.object(business_logic, "get_actor", mocker.AsyncMock())

    task = asyncio.create_task(
        business_logic.get_group_filters(
            school_classes,
            work_groups,
            mocker.AsyncMock(),
            mocker.AsyncMock(),
            ACTOR_ID,
            "school1",
            "en",
        )
    )
    # One step runs it up to the gather, whose reads are scheduled but not started.
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    school_classes.get_school_classes.assert_not_called()
    work_groups.get_work_groups.assert_not_called()
