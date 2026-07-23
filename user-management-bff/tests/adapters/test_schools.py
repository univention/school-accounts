# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import json
import os

import pytest

import user_management_bff.adapters.users
from user_management_bff.adapters.base import KelvinPersistenceAdapterSettings
from user_management_bff.adapters.schools import (
    FileSchoolsPersistenceAdapter,
    FileSchoolsPersistenceAdapterSettings,
    KelvinSchoolsPersistenceAdapter,
)
from user_management_bff.models import School


class TestKelvinSchoolsPersistenceAdapter:
    @pytest.fixture
    def adapter(self):
        return KelvinSchoolsPersistenceAdapter()

    @pytest.fixture
    def dummy_settings(self):
        return KelvinPersistenceAdapterSettings(
            url="https://test.com", username="test", password="password"
        )

    @pytest.fixture
    def make_kelvin_school_from_data(self, mocker):
        def _make_kelvin_school_from_data(school_data: dict):
            kelvin_school = mocker.MagicMock()
            kelvin_school.name = school_data["id"]
            kelvin_school.display_name = school_data["display_name"]
            return kelvin_school

        return _make_kelvin_school_from_data

    def test_get_settings_cls(self):
        assert KelvinSchoolsPersistenceAdapter.get_settings_cls() == KelvinPersistenceAdapterSettings

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
        self, adapter, dummy_settings, monkeypatch, mocker, make_kelvin_school_from_data, input_data
    ):
        class MockSchoolResource:
            async def search(self, *_args, **_kwargs):
                for user_data in input_data:
                    yield make_kelvin_school_from_data(user_data)

        mock_school_resource = mocker.MagicMock(return_value=MockSchoolResource())
        monkeypatch.setattr(user_management_bff.adapters.schools, "SchoolResource", mock_school_resource)
        await adapter.configure(dummy_settings)
        result = await adapter.get_schools()
        assert result == [
            School(id=school_data["id"], display_name=school_data["display_name"])
            for school_data in input_data
        ]


class TestFileSchoolsPersistenceAdapter:
    @pytest.fixture
    def adapter(self):
        return FileSchoolsPersistenceAdapter()

    def test_get_settings_cls(self, adapter):
        assert adapter.get_settings_cls() == FileSchoolsPersistenceAdapterSettings

    @pytest.mark.asyncio
    async def test_configure(self, adapter, tmpdir):
        data_file = tmpdir / "test_data.json"
        data = {"foo": "bar"}
        with open(data_file, "w") as fd:
            json.dump(data, fd)
        await adapter.configure(FileSchoolsPersistenceAdapterSettings(source=str(data_file)))
        assert adapter._data == data

    @pytest.fixture
    def source_path(self):
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../data/schools.json",
        )

    @pytest.mark.asyncio
    async def test_get_users(self, adapter, source_path):
        with open(source_path, "r") as fd:
            expected_schools = json.load(fd)
        await adapter.configure(FileSchoolsPersistenceAdapterSettings(source=source_path))
        result = await adapter.get_schools()
        assert result == [
            School(id=school["id"], display_name=school["display_name"]) for school in expected_schools
        ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "name,expected",
        [
            ("school2", [School(id="school2", display_name="School 2")]),
            ("NON_EXISTENT", []),
        ],
    )
    async def test_get_schools_by_name(self, adapter, source_path, name, expected):
        # A name narrows the result to that single school (no match -> empty list).
        await adapter.configure(FileSchoolsPersistenceAdapterSettings(source=source_path))
        assert await adapter.get_schools(name=name) == expected
