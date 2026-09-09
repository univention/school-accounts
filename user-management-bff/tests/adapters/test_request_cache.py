# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import pytest
from pytest_mock import MockerFixture

from user_management_bff.adapters.request_cache import (
    RequestCachedSchoolClassesAdapter,
    RequestCachedSchoolsAdapter,
    RequestCachedWorkGroupsAdapter,
)
from user_management_bff.models import School, SchoolClass, WorkGroup


@pytest.mark.asyncio
async def test_schools_are_fetched_once_per_name(mocker: MockerFixture):
    inner = mocker.AsyncMock()
    inner.get_schools.return_value = [School(id="school1", display_name="School 1")]
    adapter = RequestCachedSchoolsAdapter(inner)

    first = await adapter.get_schools()
    assert await adapter.get_schools() == first
    await adapter.get_schools("school1")

    # The unfiltered list and a named lookup are different reads, so both run,
    # but neither runs twice.
    assert inner.get_schools.call_count == 2


@pytest.mark.asyncio
async def test_school_classes_are_fetched_once_per_school(mocker: MockerFixture):
    inner = mocker.AsyncMock()
    inner.get_school_classes.return_value = [SchoolClass(id="1a", display_name="1a", school="school1")]
    adapter = RequestCachedSchoolClassesAdapter(inner)

    first = await adapter.get_school_classes("school1")
    assert await adapter.get_school_classes("school1") == first
    await adapter.get_school_classes("school2")

    assert [call.args[0] for call in inner.get_school_classes.call_args_list] == [
        "school1",
        "school2",
    ]


@pytest.mark.asyncio
async def test_work_groups_are_fetched_once_per_school(mocker: MockerFixture):
    inner = mocker.AsyncMock()
    inner.get_work_groups.return_value = [WorkGroup(id="w1a", display_name="w1a", school="school1")]
    adapter = RequestCachedWorkGroupsAdapter(inner)

    first = await adapter.get_work_groups("school1")
    assert await adapter.get_work_groups("school1") == first
    await adapter.get_work_groups("school2")

    assert [call.args[0] for call in inner.get_work_groups.call_args_list] == [
        "school1",
        "school2",
    ]


@pytest.mark.asyncio
async def test_an_empty_result_is_cached_too(mocker: MockerFixture):
    """A school without work groups must not be re-fetched on every miss."""
    inner = mocker.AsyncMock()
    inner.get_work_groups.return_value = []
    adapter = RequestCachedWorkGroupsAdapter(inner)

    assert await adapter.get_work_groups("school3") == []
    assert await adapter.get_work_groups("school3") == []

    inner.get_work_groups.assert_awaited_once_with("school3")
