# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import json
from dataclasses import dataclass, field

import aiofiles
from loguru import logger
from port_loader import AsyncConfiguredAdapterMixin
from port_loader.models import SETTINGS_NAME_METADATA
from typing_extensions import override
from ucsschool.kelvin.client import SchoolClass as KelvinSchoolClass
from ucsschool.kelvin.client import SchoolClassResource

from ..models import SchoolClass
from ..ports import SchoolClassesPersistencePort
from .base import KelvinPersistenceBaseAdapter, fetch_groups_by_name


class KelvinSchoolClassesPersistenceAdapter(SchoolClassesPersistencePort, KelvinPersistenceBaseAdapter):
    @staticmethod
    def _school_class(kelvin_school_class: KelvinSchoolClass, school: str) -> SchoolClass:
        return SchoolClass(
            id=kelvin_school_class.name,
            display_name=kelvin_school_class.description or kelvin_school_class.name,
            school=school,
        )

    @override
    async def get_school_classes(self, school: str) -> list[SchoolClass]:
        kelvin_school_classes = SchoolClassResource(session=self.kelvin_session).search(
            school=school, exclude="users"
        )
        school_classes = [
            self._school_class(school_class, school) async for school_class in kelvin_school_classes
        ]
        logger.debug(
            "Fetched school classes from the Kelvin API.", school=school, count=len(school_classes)
        )
        return school_classes

    @override
    async def get_school_classes_by_name(self, school: str, names: list[str]) -> list[SchoolClass]:
        if not names:
            return []
        resource = SchoolClassResource(session=self.kelvin_session)
        fetched = await fetch_groups_by_name(
            lambda chunk: resource.search(school=school, name=chunk, exclude="users"),
            names,
            "school_class",
            school,
        )
        return [self._school_class(group, school) for group in fetched]


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
        async with aiofiles.open(settings.source) as fd:
            self._data = json.loads(await fd.read())

    @override
    async def get_school_classes(self, school: str) -> list[SchoolClass]:
        return [
            SchoolClass(id=school_class, display_name=school_class, school=school)
            # A school with no entry has no groups; the Kelvin adapter returns an
            # empty list for that, so this one must not raise KeyError instead.
            for school_class in self._data.get(school, [])
        ]

    @override
    async def get_school_classes_by_name(self, school: str, names: list[str]) -> list[SchoolClass]:
        known = set(self._data.get(school, []))
        return [
            SchoolClass(id=school_class, display_name=school_class, school=school)
            for school_class in names
            if school_class in known
        ]
