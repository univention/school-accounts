# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import json
from dataclasses import dataclass, field

import aiofiles
from loguru import logger
from port_loader import AsyncConfiguredAdapterMixin
from port_loader.models import SETTINGS_NAME_METADATA
from typing_extensions import override
from ucsschool.kelvin.client import WorkGroup as KelvinWorkGroup
from ucsschool.kelvin.client import WorkGroupResource

from ..models import WorkGroup
from ..ports import WorkGroupsPersistencePort
from .base import KelvinPersistenceBaseAdapter, fetch_groups_by_name


class KelvinWorkGroupsPersistenceAdapter(WorkGroupsPersistencePort, KelvinPersistenceBaseAdapter):
    @staticmethod
    def _work_group(kelvin_work_group: KelvinWorkGroup, school: str) -> WorkGroup:
        return WorkGroup(
            id=kelvin_work_group.name,
            display_name=kelvin_work_group.description or kelvin_work_group.name,
            school=school,
        )

    @override
    async def get_work_groups(self, school: str) -> list[WorkGroup]:
        kelvin_work_groups = WorkGroupResource(session=self.kelvin_session).search(
            school=school, exclude="users"
        )
        work_groups = [self._work_group(work_group, school) async for work_group in kelvin_work_groups]
        logger.debug("Fetched work groups from the Kelvin API.", school=school, count=len(work_groups))
        return work_groups

    @override
    async def get_work_groups_by_name(self, school: str, names: list[str]) -> list[WorkGroup]:
        if not names:
            return []
        resource = WorkGroupResource(session=self.kelvin_session)
        fetched = await fetch_groups_by_name(
            lambda chunk: resource.search(school=school, name=chunk, exclude="users"),
            names,
            "work_group",
            school,
        )
        return [self._work_group(group, school) for group in fetched]


@dataclass
class FileWorkGroupsPersistenceAdapterSettings:
    source: str = field(metadata={SETTINGS_NAME_METADATA: "file_work_groups_persistence_adapter.source"})


class FileWorkGroupsPersistenceAdapter(
    WorkGroupsPersistencePort, AsyncConfiguredAdapterMixin[FileWorkGroupsPersistenceAdapterSettings]
):
    class Config:
        alias = "file"
        cached = True

    def __init__(self):
        self._data: dict[str, list[str]] = {}

    @classmethod
    def get_settings_cls(
        cls,
    ) -> type[FileWorkGroupsPersistenceAdapterSettings]:  # pragma: no cover
        return FileWorkGroupsPersistenceAdapterSettings

    async def configure(self, settings: FileWorkGroupsPersistenceAdapterSettings):
        async with aiofiles.open(settings.source) as fd:
            self._data = json.loads(await fd.read())

    @override
    async def get_work_groups(self, school: str) -> list[WorkGroup]:
        return [
            WorkGroup(id=work_group, display_name=work_group, school=school)
            # A school with no entry has no groups; the Kelvin adapter returns an
            # empty list for that, so this one must not raise KeyError instead.
            for work_group in self._data.get(school, [])
        ]

    @override
    async def get_work_groups_by_name(self, school: str, names: list[str]) -> list[WorkGroup]:
        known = set(self._data.get(school, []))
        return [
            WorkGroup(id=work_group, display_name=work_group, school=school)
            for work_group in names
            if work_group in known
        ]
