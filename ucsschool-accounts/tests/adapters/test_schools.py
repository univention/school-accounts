# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import json
import os
from collections.abc import Coroutine
from pathlib import Path
from typing import Any, Callable
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

import ucsschool_accounts.adapters.schools
from ucsschool_accounts.adapters.base import KelvinPersistenceAdapterSettings
from ucsschool_accounts.adapters.schools import (
    FileSchoolsPersistenceAdapter,
    FileSchoolsPersistenceAdapterSettings,
    KelvinSchoolsPersistenceAdapter,
)
from ucsschool_accounts.models import School
from ucsschool_accounts.ports import SchoolsPersistencePort


class TestKelvinSchoolsPersistenceAdapter:
    @pytest.fixture
    def adapter(self) -> KelvinSchoolsPersistenceAdapter:
        return KelvinSchoolsPersistenceAdapter()

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
        self,
        adapter: KelvinSchoolsPersistenceAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
        make_kelvin_school_from_data: Callable[[dict[str, str]], MagicMock],
        input_data: list[dict[str, str]],
    ):
        class MockSchoolResource:
            async def search(self, *_args: Any, **_kwargs: Any):
                for user_data in input_data:
                    yield make_kelvin_school_from_data(user_data)

        mock_school_resource = mocker.MagicMock(return_value=MockSchoolResource())
        monkeypatch.setattr(ucsschool_accounts.adapters.schools, "SchoolResource", mock_school_resource)
        await adapter.configure(dummy_settings)
        result = await adapter.get_schools()
        assert result == [
            School(id=school_data["id"], display_name=school_data["display_name"])
            for school_data in input_data
        ]


class TestFileSchoolsPersistenceAdapter:
    @pytest.fixture
    def adapter(self) -> FileSchoolsPersistenceAdapter:
        return FileSchoolsPersistenceAdapter()

    def test_get_settings_cls(self, adapter: FileSchoolsPersistenceAdapter):
        assert adapter.get_settings_cls() == FileSchoolsPersistenceAdapterSettings

    @pytest.mark.asyncio
    async def test_configure(self, adapter: FileSchoolsPersistenceAdapter, tmpdir: Path):
        data_file = tmpdir / "test_data.json"
        data = {"foo": "bar"}
        with open(data_file, "w") as fd:
            json.dump(data, fd)
        await adapter.configure(FileSchoolsPersistenceAdapterSettings(source=str(data_file)))
        assert adapter._data == data

    @pytest.fixture
    def source_path(self) -> str:
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../data/schools.json",
        )

    @pytest.mark.asyncio
    async def test_get_users(self, adapter: FileSchoolsPersistenceAdapter, source_path: str):
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
    async def test_get_schools_by_name(
        self, adapter: FileSchoolsPersistenceAdapter, source_path: str, name: str, expected: list[School]
    ):
        # A name narrows the result to that single school (no match -> empty list).
        await adapter.configure(FileSchoolsPersistenceAdapterSettings(source=source_path))
        assert await adapter.get_schools(name=name) == expected


# ---------------------------------------------------------------------------
# SchoolsPersistencePort contract: one matrix, run against every implementation.
#
# The name lookup is where the two can drift: the file adapter matches ids
# itself, the Kelvin adapter forwards ?name= and lets the service match. Only an
# assertion on the observable result pins them together.
# ---------------------------------------------------------------------------

CONTRACT_SCHOOLS: list[dict[str, str]] = [
    {"id": "school1", "display_name": "School 1"},
    {"id": "school2", "display_name": "School 2"},
]


@pytest.fixture(params=["file", "kelvin"])
def schools_adapter(
    request: pytest.FixtureRequest,
    tmpdir: Path,
    dummy_settings: KelvinPersistenceAdapterSettings,
    patch_kelvin_resource: Callable[[Any, str, Any], None],
    make_kelvin_school_from_data: Callable[[dict[str, str]], MagicMock],
) -> Callable[[], Coroutine[Any, Any, SchoolsPersistencePort]]:
    """Configure one implementation of SchoolsPersistencePort over CONTRACT_SCHOOLS."""

    async def _file() -> SchoolsPersistencePort:
        source = tmpdir / "contract_schools.json"
        with open(source, "w") as fd:
            json.dump(CONTRACT_SCHOOLS, fd)
        adapter = FileSchoolsPersistenceAdapter()
        await adapter.configure(FileSchoolsPersistenceAdapterSettings(source=str(source)))
        return adapter

    async def _kelvin() -> SchoolsPersistencePort:
        class MockSchoolResource:
            async def search(self, *_args: Any, name: str | None = None, **_kwargs: Any):
                # Kelvin applies ?name= itself; the adapter only forwards it.
                for school_data in CONTRACT_SCHOOLS:
                    if name is None or school_data["id"] == name:
                        yield make_kelvin_school_from_data(school_data)

        patch_kelvin_resource(
            ucsschool_accounts.adapters.schools, "SchoolResource", MockSchoolResource()
        )
        adapter = KelvinSchoolsPersistenceAdapter()
        await adapter.configure(dummy_settings)
        return adapter

    return _file if request.param == "file" else _kelvin


@pytest.mark.parametrize(
    "name,expected_ids",
    [
        pytest.param(None, ["school1", "school2"], id="no-name-returns-every-school"),
        pytest.param("school2", ["school2"], id="exact-name-returns-that-school"),
        pytest.param("NON_EXISTENT", [], id="unknown-name-returns-nothing"),
    ],
)
@pytest.mark.asyncio
async def test_get_schools_contract(
    schools_adapter: Callable[[], Coroutine[Any, Any, SchoolsPersistencePort]],
    name: str | None,
    expected_ids: list[str],
):
    adapter = await schools_adapter()
    result = await adapter.get_schools(name=name)
    assert [school.id for school in result] == expected_ids
    assert all(school.display_name for school in result)
