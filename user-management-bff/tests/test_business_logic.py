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
from user_management_bff.adapters.users import FileUsersPersistenceAdapter
from user_management_bff.business_logic import get_schools
from user_management_bff.errors import (
    NoSchoolUserError,
    ObjectNotFoundError,
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
async def test_set_passwords_success(ports: Ports, mocker: MockerFixture):
    # set_password is mocked here (rather than exercising the real File adapter write)
    # since ports.users points at the shared tests/data/users.json fixture - a real
    # write here would need its own cleanup. The write path itself is covered at the
    # adapter level (tests/adapters/test_users.py); this test is about orchestration.
    mocker.patch.object(FileUsersPersistenceAdapter, "set_password", new_callable=AsyncMock)
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
    ports: Ports, mocker: MockerFixture
):
    set_password_mock = mocker.patch.object(
        FileUsersPersistenceAdapter, "set_password", new_callable=AsyncMock
    )
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
    set_password_mock.assert_awaited_once_with("test_user1", "new-password")


@pytest.mark.asyncio
async def test_set_passwords_actor_can_include_self(ports: Ports, mocker: MockerFixture):
    mocker.patch.object(FileUsersPersistenceAdapter, "set_password", new_callable=AsyncMock)
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
    ports: Ports, mocker: MockerFixture
):
    target_ids = ["test_user1", "test_user2", "test_user3"]
    mocker.patch.object(
        FilePermissionsAdapter,
        "get_permissions",
        side_effect=_permissions_by_id({tid: [Permission.write_password] for tid in target_ids}),
    )

    async def _set_password(identifier: str, _password: str) -> None:
        if identifier == "test_user2":
            raise ObjectNotFoundError(identifier="test_user2")
        if identifier == "test_user3":
            raise PasswordResetRejectedError(identifier="test_user3", message="policy violation")

    set_password_mock = mocker.patch.object(
        FileUsersPersistenceAdapter, "set_password", side_effect=_set_password
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
async def test_set_passwords_missing_target_returns_not_found_outcome_without_aborting_others(
    ports: Ports, mocker: MockerFixture
):
    set_password_mock = mocker.patch.object(
        FileUsersPersistenceAdapter, "set_password", new_callable=AsyncMock
    )
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
    set_password_mock.assert_awaited_once_with("test_user1", "new-password")


@pytest.mark.asyncio
async def test_set_passwords_unexpected_fetch_error_still_aborts_whole_request(
    ports: Ports, mocker: MockerFixture
):
    set_password_mock = mocker.patch.object(
        FileUsersPersistenceAdapter, "set_password", new_callable=AsyncMock
    )
    original_get_user = FileUsersPersistenceAdapter.get_user

    async def _get_user(identifier: str) -> User:
        if identifier == "test_user1":
            raise RuntimeError("Kelvin is unreachable")
        return await original_get_user(ports.users, identifier)  # pyright: ignore[reportArgumentType]

    mocker.patch.object(FileUsersPersistenceAdapter, "get_user", side_effect=_get_user)
    with pytest.raises(RuntimeError, match="Kelvin is unreachable"):
        await business_logic.set_passwords(
            ports.users, ports.permissions, ACTOR_ID, ["test_user1", "test_user2"], "new-password", "en"
        )
    set_password_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_set_passwords_preserves_request_order_across_outcome_kinds(
    ports: Ports, mocker: MockerFixture
):
    mocker.patch.object(
        FilePermissionsAdapter,
        "get_permissions",
        side_effect=_permissions_by_id({"test_user1": [Permission.write_password]}),
    )
    mocker.patch.object(FileUsersPersistenceAdapter, "set_password", new_callable=AsyncMock)
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
async def test_set_passwords_deduplicates_target_ids(ports: Ports, mocker: MockerFixture):
    mocker.patch.object(
        FilePermissionsAdapter,
        "get_permissions",
        side_effect=_permissions_by_id({"test_user1": [Permission.write_password]}),
    )
    set_password_mock = mocker.patch.object(
        FileUsersPersistenceAdapter, "set_password", new_callable=AsyncMock
    )
    result = await business_logic.set_passwords(
        ports.users, ports.permissions, ACTOR_ID, ["test_user1", "test_user1"], "new-password", "en"
    )
    assert [outcome.target_id for outcome in result.outcomes] == ["test_user1"]
    set_password_mock.assert_awaited_once_with("test_user1", "new-password")


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
    ports: Ports, mocker: MockerFixture
):
    get_permissions_mock = mocker.patch.object(FilePermissionsAdapter, "get_permissions")
    get_user_mock = mocker.patch.object(FileUsersPersistenceAdapter, "get_user")
    set_password_mock = mocker.patch.object(FileUsersPersistenceAdapter, "set_password")
    result = await business_logic.set_passwords(
        ports.users, ports.permissions, ACTOR_ID, ["test_user1"], "", "en"
    )
    assert result.outcomes == []
    assert result.request_error == presentation.PasswordResetRequestError.empty_password
    get_permissions_mock.assert_not_called()
    get_user_mock.assert_not_called()
    set_password_mock.assert_not_called()


@pytest.mark.asyncio
async def test_set_passwords_too_many_targets_is_rejected_without_any_writes(
    ports: Ports, mocker: MockerFixture
):
    get_permissions_mock = mocker.patch.object(FilePermissionsAdapter, "get_permissions")
    get_user_mock = mocker.patch.object(FileUsersPersistenceAdapter, "get_user")
    set_password_mock = mocker.patch.object(FileUsersPersistenceAdapter, "set_password")
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
        async def set_password(self, identifier: str, password: str) -> None:
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
    real_get_user = FileUsersPersistenceAdapter.get_user

    async def _get_user(self: FileUsersPersistenceAdapter, identifier: str) -> User:
        # The actor is let through, so the failure comes from the gather, not get_actor.
        if identifier == ACTOR_ID:
            return await real_get_user(self, identifier)
        raise RuntimeError("kelvin is down")

    mocker.patch.object(FileUsersPersistenceAdapter, "get_user", _get_user)
    with pytest.raises(RuntimeError, match="kelvin is down"):
        await business_logic.get_password_reset_selection(
            ports.users, ports.permissions, ACTOR_ID, ["test_user1"], "en"
        )
