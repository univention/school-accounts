# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import json
from dataclasses import dataclass, field
from typing import Type

from port_loader import AsyncConfiguredAdapterMixin
from port_loader.models import SETTINGS_NAME_METADATA
from ucsschool.kelvin.client import SchoolClassResource

from ..models import SchoolClass
from ..ports import SchoolClassesPersistencePort
from .base import KelvinPersistenceBaseAdapter


class KelvinSchoolClassesPersistenceAdapter(SchoolClassesPersistencePort, KelvinPersistenceBaseAdapter):
    async def get_school_classes(self, school: str) -> list[SchoolClass]:
        async with self.kelvin_session as session:
            kelvin_school_classes = SchoolClassResource(session=session).search()
            return [
                SchoolClass(id=school_class.name, display_name=school_class.display_name)
                async for school_class in kelvin_school_classes
            ]


@dataclass
class FileSchoolClassesPersistenceAdapterSettings:
    source: str = field(
        metadata={SETTINGS_NAME_METADATA: "file_school_classes_persistence_adapter.source"}
    )


class FileSchoolClassesPersistenceAdapter(SchoolClassesPersistencePort, AsyncConfiguredAdapterMixin):
    class Config:
        alias = "file"
        cached = True

    def __init__(self):
        self._data = {}

    @classmethod
    def get_settings_cls(
        cls,
    ) -> Type[FileSchoolClassesPersistenceAdapterSettings]:  # pragma: no cover
        return FileSchoolClassesPersistenceAdapterSettings

    async def configure(self, settings: FileSchoolClassesPersistenceAdapterSettings):
        with open(settings.source, "r") as fd:
            self._data = json.load(fd)

    async def get_school_classes(self, school: str) -> list[SchoolClass]:
        return [
            SchoolClass(id=school_class, display_name=school_class)
            for school_class in self._data[school]
        ]
