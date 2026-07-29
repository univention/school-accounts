# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
"""Integration tests for the business logic.

These call ``business_logic.*`` directly using the real file-based adapters
obtained from the configured ``ADAPTER_REGISTRY`` (the registry is configured by
the app startup that the session-scoped ``test_client`` fixture triggers).
"""
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import pytest_asyncio

from user_management_bff import business_logic, presentation
from user_management_bff.adapter_registry import ADAPTER_REGISTRY
from user_management_bff.adapters.permissions import FilePermissionsAdapter
from user_management_bff.business_logic import get_schools
from user_management_bff.errors import NoSchoolUserError, ObjectNotFoundError
from user_management_bff.lang import _
from user_management_bff.models import Permission, UsersGetRequest
from user_management_bff.ports import (
    PermissionsPort,
    SchoolClassesPersistencePort,
    SchoolsPersistencePort,
    UsersPersistencePort,
    WorkGroupsPersistencePort,
)

# The actor id supplied by AlwaysAuthenticatedAdapter in the test environment.
ACTOR_ID = "dev"


async def _get_ports() -> SimpleNamespace:
    """Fetch the configured file-based adapters from the registry."""
    return SimpleNamespace(
        users=await ADAPTER_REGISTRY(UsersPersistencePort),
        schools=await ADAPTER_REGISTRY(SchoolsPersistencePort),
        school_classes=await ADAPTER_REGISTRY(SchoolClassesPersistencePort),
        work_groups=await ADAPTER_REGISTRY(WorkGroupsPersistencePort),
        permissions=await ADAPTER_REGISTRY(PermissionsPort),
    )


@pytest_asyncio.fixture
async def ports(test_client):
    # `test_client` triggers app startup, which configures the registry.
    return await _get_ports()


# ---------------------------------------------------------------------------
# Pure helpers / actor resolution
# ---------------------------------------------------------------------------
@pytest.fixture
def users_get_not_found_mock(mocker):
    users_get_mock = mocker.AsyncMock()
    users_get_mock.get_user.side_effect = ObjectNotFoundError(identifier="USER")
    return users_get_mock


@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["en", "de"])
async def test_get_schools_actor_not_found(mocker, users_get_not_found_mock, lang):
    user = "USER"
    with pytest.raises(
        NoSchoolUserError,
        match=_(f"The logged in user '{user}' is not a valid UCS@school user.", lang=lang),
    ) as exc_info:
        await get_schools(mocker.AsyncMock(), users_get_not_found_mock, "USER", lang)
    assert exc_info.value.identifier == "USER"


# ---------------------------------------------------------------------------
# get_users
# ---------------------------------------------------------------------------
async def _get_users(ports, school, *, lang="en"):
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
async def test_get_users(ports, school, expected_ids):
    result = await _get_users(ports, school)
    assert {user.id for user in result.users} == expected_ids


@pytest.mark.asyncio
@patch.object(FilePermissionsAdapter, "get_permissions", return_value={})
async def test_get_users_no_permissions(_permissions_mock, ports):
    # Users for whom the actor holds no permissions are omitted from the view.
    result = await _get_users(ports, "test_school1")
    assert presentation.build_user_list(result, "en").rows == []


# ---------------------------------------------------------------------------
# get_schools / get_school_classes / get_work_groups
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_schools(ports):
    result = await business_logic.get_schools(ports.schools, ports.users, ACTOR_ID, "en")
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
async def test_get_school_classes(ports):
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
async def test_get_work_groups(ports):
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

    def _side_effect(actor, targets):
        return {
            (target.old_target or target.new_target).id: mapping.get(
                (target.old_target or target.new_target).id, []
            )
            for target in targets
        }

    return _side_effect


# get_school_classes / get_work_groups filter out entries the actor
# may not use as a filter (the False side of the use_as_filter check).
@pytest.mark.asyncio
async def test_get_school_classes_filters_by_use_as_filter(ports, mocker):
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
async def test_get_work_groups_filters_by_use_as_filter(ports, mocker):
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
async def test_get_users_partial_visibility(ports, mocker):
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
