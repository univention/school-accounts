# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import json
from dataclasses import dataclass, field

from port_loader import AsyncConfiguredAdapterMixin
from port_loader.models import SETTINGS_NAME_METADATA
from typing_extensions import override
from ucsschool.kelvin.client import SchoolClassResource

from ..models import SchoolClass
from ..ports import SchoolClassesPersistencePort
from .base import KelvinPersistenceBaseAdapter


class KelvinSchoolClassesPersistenceAdapter(SchoolClassesPersistencePort, KelvinPersistenceBaseAdapter):
    async def get_school_classes(self, school: str) -> list[SchoolClass]:
        async with self.kelvin_session as session:
            kelvin_school_classes = SchoolClassResource(session=session).search(school=school)
            return [
                SchoolClass(
                    id=school_class.name,
                    display_name=school_class.description or school_class.name,
                    school=school,
                )
                async for school_class in kelvin_school_classes
            ]


@dataclass
class FileSchoolClassesPersistenceAdapterSettings:
    source: str = field(
        metadata={SETTINGS_NAME_METADATA: "file_school_classes_persistence_adapter.source"}
    )


class FileSchoolClassesPersistenceAdapter(
    SchoolClassesPersistencePort,
    AsyncConfiguredAdapterMixin[FileSchoolClassesPersistenceAdapterSettings],
):
    class Config:
        alias: str = "file"
        cached: bool = True

    def __init__(self):
        self._data: dict[str, list[str]] = {}

    @classmethod
    @override
    def get_settings_cls(
        cls,
    ) -> type[FileSchoolClassesPersistenceAdapterSettings]:  # pragma: no cover
        return FileSchoolClassesPersistenceAdapterSettings

    @override
    async def configure(self, settings: FileSchoolClassesPersistenceAdapterSettings):
        with open(settings.source, "r") as fd:
            self._data = json.load(fd)

    @override
    async def get_school_classes(self, school: str) -> list[SchoolClass]:
        return [
            SchoolClass(id=school_class, display_name=school_class, school=school)
            # A school with no entry has no groups; the Kelvin adapter returns an
            # empty list for that, so this one must not raise KeyError instead.
            for school_class in self._data.get(school, [])
        ]
