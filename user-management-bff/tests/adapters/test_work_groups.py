# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import json
import os

import pytest

import user_management_bff.adapters.users
from user_management_bff.adapters.base import KelvinPersistenceAdapterSettings
from user_management_bff.adapters.work_groups import (
    FileWorkGroupsPersistenceAdapter,
    FileWorkGroupsPersistenceAdapterSettings,
    KelvinWorkGroupsPersistenceAdapter,
)
from user_management_bff.models import WorkGroup


class TestKelvinWorkGroupsPersistenceAdapter:
    @pytest.fixture
    def adapter(self):
        return KelvinWorkGroupsPersistenceAdapter()

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
            kelvin_school.description = school_data["display_name"]
            return kelvin_school

        return _make_kelvin_school_from_data

    def test_get_settings_cls(self):
        assert KelvinWorkGroupsPersistenceAdapter.get_settings_cls() == KelvinPersistenceAdapterSettings

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
        class MockSchoolClassResource:
            async def search(self, *_args, **_kwargs):
                for user_data in input_data:
                    yield make_kelvin_school_from_data(user_data)

        mock_school_resource = mocker.MagicMock(return_value=MockSchoolClassResource())
        monkeypatch.setattr(
            user_management_bff.adapters.school_classes, "SchoolClassResource", mock_school_resource
        )
        monkeypatch.setattr(
            user_management_bff.adapters.work_groups, "WorkGroupResource", mock_school_resource
        )
        await adapter.configure(dummy_settings)
        result = await adapter.get_work_groups("school1")
        assert result == [
            WorkGroup(id=school_data["id"], display_name=school_data["display_name"], school="school1")
            for school_data in input_data
        ]


class TestFileWorkGroupsPersistenceAdapter:
    @pytest.fixture
    def adapter(self):
        return FileWorkGroupsPersistenceAdapter()

    def test_get_settings_cls(self, adapter):
        assert adapter.get_settings_cls() == FileWorkGroupsPersistenceAdapterSettings

    @pytest.mark.asyncio
    async def test_configure(self, adapter, tmpdir):
        data_file = tmpdir / "test_data.json"
        data = {"foo": "bar"}
        with open(data_file, "w") as fd:
            json.dump(data, fd)
        await adapter.configure(FileWorkGroupsPersistenceAdapterSettings(source=str(data_file)))
        assert adapter._data == data

    @pytest.mark.asyncio
    async def test_get_users(self, adapter):
        source_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../data/work_groups.json",
        )
        with open(source_path, "r") as fd:
            expected_work_groups = json.load(fd)["school1"]
        await adapter.configure(FileWorkGroupsPersistenceAdapterSettings(source=source_path))
        result = await adapter.get_work_groups("school1")
        assert result == [
            WorkGroup(id=work_group, display_name=work_group, school="school1")
            for work_group in expected_work_groups
        ]
