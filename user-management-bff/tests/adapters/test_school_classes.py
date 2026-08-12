# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import json
import os
from pathlib import Path
from typing import Any, Callable
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

import user_management_bff.adapters.school_classes
from user_management_bff.adapters.base import KelvinPersistenceAdapterSettings
from user_management_bff.adapters.school_classes import (
    FileSchoolClassesPersistenceAdapter,
    FileSchoolClassesPersistenceAdapterSettings,
    KelvinSchoolClassesPersistenceAdapter,
)
from user_management_bff.models import SchoolClass


class TestKelvinSchoolClassesPersistenceAdapter:
    @pytest.fixture
    def adapter(self) -> KelvinSchoolClassesPersistenceAdapter:
        return KelvinSchoolClassesPersistenceAdapter()

    @pytest.fixture
    def dummy_settings(self) -> KelvinPersistenceAdapterSettings:
        return KelvinPersistenceAdapterSettings(
            url="https://test.com", username="test", password="password"
        )

    @pytest.fixture
    def make_kelvin_school_from_data(
        self, mocker: MockerFixture
    ) -> Callable[[dict[str, str]], MagicMock]:
        def _make_kelvin_school_from_data(school_data: dict[str, str]) -> MagicMock:
            kelvin_school = mocker.MagicMock()
            kelvin_school.name = school_data["id"]
            kelvin_school.description = school_data["display_name"]
            return kelvin_school

        return _make_kelvin_school_from_data

    def test_get_settings_cls(self):
        assert (
            KelvinSchoolClassesPersistenceAdapter.get_settings_cls() == KelvinPersistenceAdapterSettings
        )

    @pytest.mark.parametrize(
        "input_data",
        [
            [],
            [{"id": "school1", "display_name": "School 1"}],
            [
                {"id": "school1", "display_name": "School 1"},
                {"id": "school2", "display_name": "School 2"},
            ],
        ],
    )
    @pytest.mark.asyncio
    async def test_get_users(
        self,
        adapter: KelvinSchoolClassesPersistenceAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
        make_kelvin_school_from_data: Callable[[dict[str, str]], MagicMock],
        input_data: list[dict[str, str]],
    ):
        class MockSchoolClassResource:
            async def search(self, *_args: Any, **_kwargs: Any):
                for user_data in input_data:
                    yield make_kelvin_school_from_data(user_data)

        mock_school_resource = mocker.MagicMock(return_value=MockSchoolClassResource())
        monkeypatch.setattr(
            user_management_bff.adapters.school_classes, "SchoolClassResource", mock_school_resource
        )
        await adapter.configure(dummy_settings)
        result = await adapter.get_school_classes("school1")
        assert result == [
            SchoolClass(id=school_data["id"], display_name=school_data["display_name"], school="school1")
            for school_data in input_data
        ]


class TestFileSchoolClassesPersistenceAdapter:
    @pytest.fixture
    def adapter(self) -> FileSchoolClassesPersistenceAdapter:
        return FileSchoolClassesPersistenceAdapter()

    def test_get_settings_cls(self, adapter: FileSchoolClassesPersistenceAdapter):
        assert adapter.get_settings_cls() == FileSchoolClassesPersistenceAdapterSettings

    @pytest.mark.asyncio
    async def test_configure(self, adapter: FileSchoolClassesPersistenceAdapter, tmpdir: Path):
        data_file = tmpdir / "test_data.json"
        data = {"foo": "bar"}
        with open(data_file, "w") as fd:
            json.dump(data, fd)
        await adapter.configure(FileSchoolClassesPersistenceAdapterSettings(source=str(data_file)))
        assert adapter._data == data

    @pytest.mark.asyncio
    async def test_get_users(self, adapter: FileSchoolClassesPersistenceAdapter):
        source_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../data/school_classes.json",
        )
        with open(source_path, "r") as fd:
            expected_school_classes = json.load(fd)["school1"]
        await adapter.configure(FileSchoolClassesPersistenceAdapterSettings(source=source_path))
        result = await adapter.get_school_classes("school1")
        assert result == [
            SchoolClass(id=school_class, display_name=school_class, school="school1")
            for school_class in expected_school_classes
        ]
