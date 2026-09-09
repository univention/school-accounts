# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import json
from dataclasses import dataclass, field
from typing import Optional, Type

from loguru import logger
from port_loader import AsyncConfiguredAdapterMixin
from port_loader.models import SETTINGS_NAME_METADATA
from typing_extensions import override
from ucsschool.kelvin.client import SchoolResource

from ..models import School
from ..ports import SchoolsPersistencePort
from .base import KelvinPersistenceBaseAdapter


class KelvinSchoolsPersistenceAdapter(SchoolsPersistencePort, KelvinPersistenceBaseAdapter):
    async def get_schools(self, name: Optional[str] = None) -> list[School]:
        search_kwargs = {"name": name} if name else {}
        logger.debug("Fetching schools from Kelvin API.", search_kwargs=search_kwargs)
        kelvin_schools = SchoolResource(session=self.kelvin_session).search(**search_kwargs)
        return [
            School(id=kelvin_school.name, display_name=kelvin_school.display_name or kelvin_school.name)
            async for kelvin_school in kelvin_schools
        ]


@dataclass
class FileSchoolsPersistenceAdapterSettings:
    source: str = field(metadata={SETTINGS_NAME_METADATA: "file_schools_persistence_adapter.source"})


class FileSchoolsPersistenceAdapter(
    SchoolsPersistencePort, AsyncConfiguredAdapterMixin[FileSchoolsPersistenceAdapterSettings]
):
    class Config:
        alias: str = "file"
        cached: bool = True

    def __init__(self):
        self._data = {}

    @classmethod
    @override
    def get_settings_cls(
        cls,
    ) -> Type[FileSchoolsPersistenceAdapterSettings]:  # pragma: no cover
        return FileSchoolsPersistenceAdapterSettings

    @override
    async def configure(self, settings: FileSchoolsPersistenceAdapterSettings):
        with open(settings.source, "r") as fd:
            self._data = json.load(fd)

    @override
    async def get_schools(self, name: Optional[str] = None) -> list[School]:
        if name:
            return [
                School(id=school["id"], display_name=school["display_name"])
                for school in self._data
                if school["id"] == name
            ]

        return [School(id=school["id"], display_name=school["display_name"]) for school in self._data]
