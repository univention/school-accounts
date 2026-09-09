# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Port decorators that memoize a read for the lifetime of one request.

The list route needs the same school-scoped data twice: once to build the filter
sidebar, and once to turn the group ids on a user into the display names the
table shows. Kelvin has no bulk lookup for either - a group's description comes
either from a school-scoped search or from one GET per group - so a school-scoped
search shared by both callers is the cheapest way to serve them, and neither
caller has to know the other exists.

Deliberately per request, not a process-wide cache: a group renamed in Kelvin
has to appear on the next reload, and there is no invalidation channel that
would keep a longer-lived cache honest.

These wrap whichever adapter ``USER_MANAGEMENT__ADAPTER__*`` selected, so they
are applied in the DI layer (``routes.py``) instead of being registered as
adapters themselves.
"""

from typing_extensions import override

from ..models import School, SchoolClass, WorkGroup
from ..ports import (
    SchoolClassesPersistencePort,
    SchoolsPersistencePort,
    WorkGroupsPersistencePort,
)

# The caches below are plain dicts rather than task-based single-flight: the
# duplicate reads this exists for are sequential, and two concurrent reads of the
# same key would only cost the extra request they cost today.


class RequestCachedSchoolsAdapter(SchoolsPersistencePort):
    _adapter: SchoolsPersistencePort

    def __init__(self, adapter: SchoolsPersistencePort):
        self._adapter = adapter
        self._cache: dict[str | None, list[School]] = {}

    @override
    async def get_schools(self, name: str | None = None) -> list[School]:
        if name not in self._cache:
            self._cache[name] = await self._adapter.get_schools(name)
        return self._cache[name]


class RequestCachedSchoolClassesAdapter(SchoolClassesPersistencePort):
    _adapter: SchoolClassesPersistencePort

    def __init__(self, adapter: SchoolClassesPersistencePort):
        self._adapter = adapter
        self._cache: dict[str, list[SchoolClass]] = {}

    @override
    async def get_school_classes(self, school: str) -> list[SchoolClass]:
        if school not in self._cache:
            self._cache[school] = await self._adapter.get_school_classes(school)
        return self._cache[school]


class RequestCachedWorkGroupsAdapter(WorkGroupsPersistencePort):
    _adapter: WorkGroupsPersistencePort

    def __init__(self, adapter: WorkGroupsPersistencePort):
        self._adapter = adapter
        self._cache: dict[str, list[WorkGroup]] = {}

    @override
    async def get_work_groups(self, school: str) -> list[WorkGroup]:
        if school not in self._cache:
            self._cache[school] = await self._adapter.get_work_groups(school)
        return self._cache[school]
