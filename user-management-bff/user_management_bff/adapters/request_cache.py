# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Port decorators that memoize a read for the lifetime of one request.

The list route can need the same school's data twice: once as the whole set, to
build the filter sidebar, and once as the selected group, to confirm the school
still has it. The two overlap but neither contains the other, so the group
caches here are keyed per group and the whole-school read populates them - which
makes the second read of a school the sidebar already loaded free.

Deliberately per request, not a process-wide cache: a group renamed in Kelvin
has to appear on the next reload, and there is no invalidation channel that
would keep a longer-lived cache honest.

These wrap whichever adapter ``USER_MANAGEMENT__ADAPTER__*`` selected, so they
are applied in the DI layer (``routes.py``) instead of being registered as
adapters themselves.
"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Generic, TypeVar

from typing_extensions import override

from ..models import School, SchoolClass, WorkGroup
from ..ports import (
    SchoolClassesPersistencePort,
    SchoolsPersistencePort,
    WorkGroupsPersistencePort,
)

_Group = TypeVar("_Group", SchoolClass, WorkGroup)
_Key = TypeVar("_Key")
_Value = TypeVar("_Value")


class _SingleFlight(Generic[_Key, _Value]):
    """Run at most one ``fetch`` per key, however many callers ask concurrently.

    The route builds the sidebar while the listing runs, and both can read the
    same school, so a cache of finished results would still let the second read
    start before the first one lands. Keeping the task, not its value, is what
    collapses them into one request.
    """

    _fetch: Callable[[_Key], Awaitable[_Value]]

    def __init__(self, fetch: Callable[[_Key], Awaitable[_Value]]):
        self._fetch = fetch
        self._tasks: dict[_Key, asyncio.Task[_Value]] = {}

    def started(self, key: _Key) -> bool:
        return key in self._tasks

    async def get(self, key: _Key) -> _Value:
        task = self._tasks.get(key)
        if task is None:
            # ensure_future, not create_task: the port methods are typed as
            # returning an Awaitable, and only the task is worth keeping.
            task = asyncio.ensure_future(self._fetch(key))
            self._tasks[key] = task
        return await task


class RequestCachedSchoolsAdapter(SchoolsPersistencePort):
    def __init__(self, adapter: SchoolsPersistencePort):
        self._cache: _SingleFlight[str | None, list[School]] = _SingleFlight(adapter.get_schools)

    @override
    async def get_schools(self, name: str | None = None) -> list[School]:
        return await self._cache.get(name)


class _GroupCache(Generic[_Group]):
    """One group kind's two read shapes, memoized against each other."""

    _fetch_named: Callable[[str, list[str]], Awaitable[list[_Group]]]

    def __init__(
        self,
        fetch_all: Callable[[str], Awaitable[list[_Group]]],
        fetch_named: Callable[[str, list[str]], Awaitable[list[_Group]]],
    ):
        self._fetch_named = fetch_named
        self._complete: _SingleFlight[str, list[_Group]] = _SingleFlight(fetch_all)
        self._by_name: dict[tuple[str, str], _Group] = {}

    async def all_of(self, school: str) -> list[_Group]:
        groups = await self._complete.get(school)
        for group in groups:
            self._by_name[school, group.id] = group
        return groups

    async def named(self, school: str, names: list[str]) -> list[_Group]:
        missing = [name for name in names if (school, name) not in self._by_name]
        if missing:
            # Reading the whole school already answers for a name still missing
            # afterwards: it does not exist, and asking again would not change
            # that. Otherwise the names are asked for directly, which is one
            # request however many of them there are.
            if self._complete.started(school):
                await self.all_of(school)
            else:
                for group in await self._fetch_named(school, missing):
                    self._by_name[school, group.id] = group
        return [self._by_name[school, name] for name in names if (school, name) in self._by_name]


class RequestCachedSchoolClassesAdapter(SchoolClassesPersistencePort):
    def __init__(self, adapter: SchoolClassesPersistencePort):
        self._cache: _GroupCache[SchoolClass] = _GroupCache(
            adapter.get_school_classes, adapter.get_school_classes_by_name
        )

    @override
    async def get_school_classes(self, school: str) -> list[SchoolClass]:
        return await self._cache.all_of(school)

    @override
    async def get_school_classes_by_name(self, school: str, names: list[str]) -> list[SchoolClass]:
        return await self._cache.named(school, names)


class RequestCachedWorkGroupsAdapter(WorkGroupsPersistencePort):
    def __init__(self, adapter: WorkGroupsPersistencePort):
        self._cache: _GroupCache[WorkGroup] = _GroupCache(
            adapter.get_work_groups, adapter.get_work_groups_by_name
        )

    @override
    async def get_work_groups(self, school: str) -> list[WorkGroup]:
        return await self._cache.all_of(school)

    @override
    async def get_work_groups_by_name(self, school: str, names: list[str]) -> list[WorkGroup]:
        return await self._cache.named(school, names)
