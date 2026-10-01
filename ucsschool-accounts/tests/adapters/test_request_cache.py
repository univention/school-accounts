# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import asyncio

import pytest
from pytest_mock import MockerFixture

from ucsschool_accounts.adapters.request_cache import (
    RequestCachedSchoolClassesAdapter,
    RequestCachedSchoolsAdapter,
    RequestCachedWorkGroupsAdapter,
)
from ucsschool_accounts.models import School, SchoolClass, WorkGroup

SCHOOL_CLASSES = [
    SchoolClass(id="1a", display_name="Class 1a", school="school1"),
    SchoolClass(id="2b", display_name="Class 2b", school="school1"),
]
WORK_GROUPS = [
    WorkGroup(id="w1a", display_name="Choir", school="school1"),
    WorkGroup(id="w2b", display_name="Chess", school="school1"),
]


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
    inner.get_school_classes.return_value = SCHOOL_CLASSES
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
    inner.get_work_groups.return_value = WORK_GROUPS
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


@pytest.mark.asyncio
async def test_the_whole_school_read_answers_later_lookups_by_name(mocker: MockerFixture):
    """The sidebar loads the selected school in full, so the table's names for that
    school are already known and must not be fetched again."""
    inner = mocker.AsyncMock()
    inner.get_work_groups.return_value = WORK_GROUPS
    adapter = RequestCachedWorkGroupsAdapter(inner)

    await adapter.get_work_groups("school1")
    assert [group.id for group in await adapter.get_work_groups_by_name("school1", ["w2b"])] == ["w2b"]

    inner.get_work_groups_by_name.assert_not_awaited()


@pytest.mark.asyncio
async def test_a_name_the_whole_school_does_not_have_is_not_looked_up(mocker: MockerFixture):
    """Holding the full list already answers for a missing name: it does not exist."""
    inner = mocker.AsyncMock()
    inner.get_school_classes.return_value = SCHOOL_CLASSES
    adapter = RequestCachedSchoolClassesAdapter(inner)

    await adapter.get_school_classes("school1")
    assert await adapter.get_school_classes_by_name("school1", ["GONE"]) == []

    inner.get_school_classes_by_name.assert_not_awaited()


@pytest.mark.asyncio
async def test_only_the_names_not_yet_known_are_fetched(mocker: MockerFixture):
    def _fetch(school: str, names: list[str]) -> list[SchoolClass]:
        return [SchoolClass(id=name, display_name=f"Class {name}", school=school) for name in names]

    inner = mocker.AsyncMock()
    inner.get_school_classes_by_name.side_effect = _fetch
    adapter = RequestCachedSchoolClassesAdapter(inner)

    await adapter.get_school_classes_by_name("school1", ["1a"])
    result = await adapter.get_school_classes_by_name("school1", ["1a", "2b"])

    # Both come back, in the order asked for, but only the new one was fetched.
    assert [school_class.id for school_class in result] == ["1a", "2b"]
    assert [call.args for call in inner.get_school_classes_by_name.call_args_list] == [
        ("school1", ["1a"]),
        ("school1", ["2b"]),
    ]


@pytest.mark.asyncio
async def test_a_name_lookup_is_scoped_to_its_school(mocker: MockerFixture):
    """Two schools can hold a class of the same name, so the cache key is the pair."""

    def _fetch(school: str, names: list[str]) -> list[SchoolClass]:
        return [
            SchoolClass(id=name, display_name=f"{name} of {school}", school=school) for name in names
        ]

    inner = mocker.AsyncMock()
    inner.get_school_classes_by_name.side_effect = _fetch
    adapter = RequestCachedSchoolClassesAdapter(inner)

    await adapter.get_school_classes_by_name("school1", ["1a"])
    result = await adapter.get_school_classes_by_name("school2", ["1a"])

    assert [school_class.display_name for school_class in result] == ["1a of school2"]
    assert [call.args for call in inner.get_school_classes_by_name.call_args_list] == [
        ("school1", ["1a"]),
        ("school2", ["1a"]),
    ]


@pytest.mark.asyncio
async def test_two_concurrent_reads_of_a_school_share_one_request(mocker: MockerFixture):
    """The page starts the filter control and the table at once, and both read the
    selected school: a cache of finished results would still let the second start."""
    started = asyncio.Event()
    release = asyncio.Event()

    async def _fetch(_school: str) -> list[SchoolClass]:
        started.set()
        await release.wait()
        return SCHOOL_CLASSES

    inner = mocker.AsyncMock()
    inner.get_school_classes.side_effect = _fetch
    adapter = RequestCachedSchoolClassesAdapter(inner)

    first = asyncio.ensure_future(adapter.get_school_classes("school1"))
    await started.wait()
    second = asyncio.ensure_future(adapter.get_school_classes("school1"))
    release.set()

    assert await first == await second == SCHOOL_CLASSES
    inner.get_school_classes.assert_awaited_once()


@pytest.mark.asyncio
async def test_a_name_lookup_waits_for_a_whole_school_read_already_running(mocker: MockerFixture):
    """Firing the per-name lookups next to the whole-school read would undo the
    saving the cache exists for, one round trip per name."""
    started = asyncio.Event()
    release = asyncio.Event()

    async def _fetch(_school: str) -> list[SchoolClass]:
        started.set()
        await release.wait()
        return SCHOOL_CLASSES

    inner = mocker.AsyncMock()
    inner.get_school_classes.side_effect = _fetch
    adapter = RequestCachedSchoolClassesAdapter(inner)

    whole = asyncio.ensure_future(adapter.get_school_classes("school1"))
    await started.wait()
    named = asyncio.ensure_future(adapter.get_school_classes_by_name("school1", ["2b"]))
    await asyncio.sleep(0)
    release.set()

    await whole
    assert [school_class.id for school_class in await named] == ["2b"]
    inner.get_school_classes_by_name.assert_not_awaited()
