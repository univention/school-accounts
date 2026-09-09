# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import json
from dataclasses import dataclass, field

from port_loader import AsyncConfiguredAdapterMixin
from port_loader.models import SETTINGS_NAME_METADATA
from ucsschool.kelvin.client import WorkGroupResource

from ..models import WorkGroup
from ..ports import WorkGroupsPersistencePort
from .base import KelvinPersistenceBaseAdapter


class KelvinWorkGroupsPersistenceAdapter(WorkGroupsPersistencePort, KelvinPersistenceBaseAdapter):
    async def get_work_groups(self, school: str) -> list[WorkGroup]:
        kelvin_work_groups = WorkGroupResource(session=self.kelvin_session).search(school=school)
        return [
            WorkGroup(
                id=work_group.name,
                display_name=work_group.description or work_group.name,
                school=school,
            )
            async for work_group in kelvin_work_groups
        ]


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
        with open(settings.source, "r") as fd:
            self._data = json.load(fd)

    async def get_work_groups(self, school: str) -> list[WorkGroup]:
        return [
            WorkGroup(id=work_group, display_name=work_group, school=school)
            # A school with no entry has no groups; the Kelvin adapter returns an
            # empty list for that, so this one must not raise KeyError instead.
            for work_group in self._data.get(school, [])
        ]
