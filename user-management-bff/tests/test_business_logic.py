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

from user_management_bff import business_logic, presentation
from user_management_bff.adapter_registry import ADAPTER_REGISTRY
from user_management_bff.adapters.permissions import FilePermissionsAdapter
from user_management_bff.adapters.school_classes import FileSchoolClassesPersistenceAdapter
from user_management_bff.adapters.users import FileUsersPersistenceAdapter
from user_management_bff.business_logic import get_schools
from user_management_bff.constants import USER_LIST_GROUPS_SHOWN
from user_management_bff.errors import (
    NoSchoolUserError,
    ObjectNotFoundError,
    PasswordChangeOnNextLoginUnsupportedError,
    PasswordResetRejectedError,
)
from user_management_bff.lang import _
from user_management_bff.models import Permission, Target, User, UserAttributes, UsersGetRequest
from user_management_bff.ports import (
    PermissionsPort,
    SchoolClassesPersistencePort,
    SchoolsPersistencePort,
    UsersPersistencePort,
    WorkGroupsPersistencePort,
)
from user_management_bff.presentation import PasswordResetOutcomeCode

# The actor id supplied by AlwaysAuthenticatedAdapter in the test environment.
ACTOR_ID = "dev"


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
    with pytest.raises(NoSchoolUserError, match=re.escape(expected)) as exc_info:
        await get_schools(mocker.AsyncMock(), mocker.AsyncMock(), users_get_not_found_mock, "USER", lang)
    assert exc_info.value.identifier == "USER"


# ---------------------------------------------------------------------------
# get_users
# ---------------------------------------------------------------------------
async def _get_users(ports: Ports, school: str, *, lang: str = "en"):
    return await business_logic.get_users(
        ports.users,
        ports.schools,
        ports.school_classes,
        ports.work_groups,
        ports.permissions,
        ACTOR_ID,
        UsersGetRequest(school=school, school_classes=[], work_groups=[]),
        lang,
    )


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
async def test_get_users_looks_up_only_the_groups_the_rows_render(ports: Ports, mocker: MockerFixture):
    all_classes_spy = mocker.spy(ports.school_classes, "get_school_classes")
    all_work_groups_spy = mocker.spy(ports.work_groups, "get_work_groups")
    classes_spy = mocker.spy(ports.school_classes, "get_school_classes_by_name")
    work_groups_spy = mocker.spy(ports.work_groups, "get_work_groups_by_name")
    await _get_users(ports, "test_school2")
    # test_user3 is listed for test_school2 but holds classes in test_school1, and the
    # list renders those with their display names - hence more than the selected school,
    # but not all seven of them. Only the names on those users are asked for, never a
    # whole school: the whole-school lookup ships every group with its full membership.
    assert [call.args for call in classes_spy.call_args_list] == [
        ("test_school1", ["1a", "2b"]),
        ("test_school2", ["1a", "2b", "3c"]),
    ]
    assert [call.args for call in work_groups_spy.call_args_list] == [("test_school2", ["w1a"])]
    all_classes_spy.assert_not_called()
    all_work_groups_spy.assert_not_called()


@pytest.mark.asyncio
@patch.object(
    FilePermissionsAdapter,
    "get_permissions",
    return_value={"test_user2": [Permission.read_last_name]},
)
async def test_get_users_group_lookups_skip_users_the_actor_cannot_see(
    _permissions_mock: MagicMock, ports: Ports, mocker: MockerFixture
):
    classes_spy = mocker.spy(ports.school_classes, "get_school_classes_by_name")
    work_groups_spy = mocker.spy(ports.work_groups, "get_work_groups_by_name")
    result = await _get_users(ports, "test_school2")
    # test_school1 is only reachable through test_user3, who is now invisible, so
    # nothing renders their groups and nothing looks them up either - and 3c drops
    # out of the test_school2 lookup with them.
    assert [user.id for user in result.users] == ["test_user2"]
    assert [call.args for call in classes_spy.call_args_list] == [("test_school2", ["1a", "2b"])]
    assert [call.args for call in work_groups_spy.call_args_list] == [("test_school2", ["w1a"])]


@pytest.mark.asyncio
@patch.object(FilePermissionsAdapter, "get_permissions", return_value={})
async def test_get_users_no_permissions(_permissions_mock: MagicMock, ports: Ports):
    # Users for whom the actor holds no permissions are omitted from the view.
    result = await _get_users(ports, "test_school1")
    assert presentation.build_user_list(result, "en").rows == []


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
    view = presentation.build_user_list(result, "en")
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
async def test_fetch_groups_asks_only_for_the_names_the_row_shows(ports: Ports, mocker: MockerFixture):
    """A user in every class of their school would otherwise pull the whole
    school in to resolve display names for a cell that is capped anyway."""
    by_name_spy = mocker.spy(FileSchoolClassesPersistenceAdapter, "get_school_classes_by_name")
    crowded = User(
        id="crowded",
        attributes=UserAttributes(
            last_name="Klein",
            first_name="Kim",
            username="crowded",
            disabled=False,
            schools=["school1"],
            school_classes={"school1": [f"c{index}" for index in range(USER_LIST_GROUPS_SHOWN + 20)]},
            work_groups={},
            roles=[],
        ),
    )

    await business_logic._fetch_groups(ports.school_classes, ports.work_groups, [crowded])

    # ``args[0]`` is the adapter instance - this spies on the class.
    assert [call.args[2] for call in by_name_spy.call_args_list] == [
        sorted(f"c{index}" for index in range(USER_LIST_GROUPS_SHOWN))
    ]
