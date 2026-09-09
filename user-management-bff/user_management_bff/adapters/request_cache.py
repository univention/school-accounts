# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Port decorators that memoize a read for the lifetime of one request.

The list route needs the same school's data twice: once as the whole set, to
build the filter sidebar, and once as the handful of groups a listed user is in,
to render their display names. The two overlap but neither contains the other, so
the group caches here are keyed per group and the whole-school read populates
them - which makes the second read of a school the sidebar already loaded free.

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
        self._complete: dict[str, list[SchoolClass]] = {}
        self._by_name: dict[tuple[str, str], SchoolClass] = {}

    @override
    async def get_school_classes(self, school: str) -> list[SchoolClass]:
        if school not in self._complete:
            classes = await self._adapter.get_school_classes(school)
            self._complete[school] = classes
            for school_class in classes:
                self._by_name[school, school_class.id] = school_class
        return self._complete[school]

    @override
    async def get_school_classes_by_name(self, school: str, names: list[str]) -> list[SchoolClass]:
        missing = [name for name in names if (school, name) not in self._by_name]
        # Holding the whole school already answers for a name that is still
        # missing: it does not exist, and asking again would not change that.
        if missing and school not in self._complete:
            for school_class in await self._adapter.get_school_classes_by_name(school, missing):
                self._by_name[school, school_class.id] = school_class
        return [self._by_name[school, name] for name in names if (school, name) in self._by_name]


class RequestCachedWorkGroupsAdapter(WorkGroupsPersistencePort):
    _adapter: WorkGroupsPersistencePort

    def __init__(self, adapter: WorkGroupsPersistencePort):
        self._adapter = adapter
        self._complete: dict[str, list[WorkGroup]] = {}
        self._by_name: dict[tuple[str, str], WorkGroup] = {}

    @override
    async def get_work_groups(self, school: str) -> list[WorkGroup]:
        if school not in self._complete:
            groups = await self._adapter.get_work_groups(school)
            self._complete[school] = groups
            for work_group in groups:
                self._by_name[school, work_group.id] = work_group
        return self._complete[school]

    @override
    async def get_work_groups_by_name(self, school: str, names: list[str]) -> list[WorkGroup]:
        missing = [name for name in names if (school, name) not in self._by_name]
        # See RequestCachedSchoolClassesAdapter.get_school_classes_by_name.
        if missing and school not in self._complete:
            for work_group in await self._adapter.get_work_groups_by_name(school, missing):
                self._by_name[school, work_group.id] = work_group
        return [self._by_name[school, name] for name in names if (school, name) in self._by_name]
