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

import user_management_bff.adapters.school_classes
import user_management_bff.adapters.work_groups
from user_management_bff.adapters.base import KelvinPersistenceAdapterSettings
from user_management_bff.adapters.work_groups import (
    FileWorkGroupsPersistenceAdapter,
    FileWorkGroupsPersistenceAdapterSettings,
    KelvinWorkGroupsPersistenceAdapter,
)
from user_management_bff.models import WorkGroup
from user_management_bff.ports import WorkGroupsPersistencePort


class TestKelvinWorkGroupsPersistenceAdapter:
    @pytest.fixture
    def adapter(self) -> KelvinWorkGroupsPersistenceAdapter:
        return KelvinWorkGroupsPersistenceAdapter()

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
        self,
        adapter: KelvinWorkGroupsPersistenceAdapter,
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
    def adapter(self) -> FileWorkGroupsPersistenceAdapter:
        return FileWorkGroupsPersistenceAdapter()

    def test_get_settings_cls(self, adapter: FileWorkGroupsPersistenceAdapter):
        assert adapter.get_settings_cls() == FileWorkGroupsPersistenceAdapterSettings

    @pytest.mark.asyncio
    async def test_configure(self, adapter: FileWorkGroupsPersistenceAdapter, tmpdir: Path):
        data_file = tmpdir / "test_data.json"
        data = {"foo": "bar"}
        with open(data_file, "w") as fd:
            json.dump(data, fd)
        await adapter.configure(FileWorkGroupsPersistenceAdapterSettings(source=str(data_file)))
        assert adapter._data == data

    @pytest.mark.asyncio
    async def test_get_users(self, adapter: FileWorkGroupsPersistenceAdapter):
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


# ---------------------------------------------------------------------------
# WorkGroupsPersistencePort contract: one matrix, run against every implementation.
#
# The file format is {school: [name, ...]} with nowhere to put a description,
# so the dataset gives the Kelvin fake description=None and the contract asserts
# the display-name fallback both adapters implement. The description-present case
# stays in the Kelvin-only test above.
# ---------------------------------------------------------------------------

CONTRACT_WORK_GROUPS: dict[str, list[str]] = {
    "school1": ["w1a", "w2b"],
    # A school that has none at all -- the case the file adapter used to raise
    # KeyError on, while the Kelvin adapter returned an empty list.
    "school2": [],
}


@pytest.fixture(params=["file", "kelvin"])
def work_groups_adapter(
    request: pytest.FixtureRequest,
    tmpdir: Path,
    dummy_settings: KelvinPersistenceAdapterSettings,
    patch_kelvin_resource: Callable[[Any, str, Any], None],
    make_kelvin_group_from_data: Callable[[str, str | None], MagicMock],
) -> Callable[[], Coroutine[Any, Any, WorkGroupsPersistencePort]]:
    """Configure one implementation of WorkGroupsPersistencePort over CONTRACT_WORK_GROUPS."""

    async def _file() -> WorkGroupsPersistencePort:
        source = tmpdir / "contract_work_groups.json"
        with open(source, "w") as fd:
            json.dump(CONTRACT_WORK_GROUPS, fd)
        adapter = FileWorkGroupsPersistenceAdapter()
        await adapter.configure(FileWorkGroupsPersistenceAdapterSettings(source=str(source)))
        return adapter

    async def _kelvin() -> WorkGroupsPersistencePort:
        class MockResource:
            async def search(self, *_args: Any, school: str = "", **_kwargs: Any):
                # Kelvin applies ?school= itself, so the adapter is not credited
                # with work the real service does for it.
                for name in CONTRACT_WORK_GROUPS.get(school, []):
                    yield make_kelvin_group_from_data(name, None)

        patch_kelvin_resource(
            user_management_bff.adapters.work_groups, "WorkGroupResource", MockResource()
        )
        adapter = KelvinWorkGroupsPersistenceAdapter()
        await adapter.configure(dummy_settings)
        return adapter

    return _file if request.param == "file" else _kelvin


@pytest.mark.parametrize(
    "school,expected_ids",
    [
        pytest.param("school1", ["w1a", "w2b"], id="returns-every-group-of-the-school"),
        pytest.param("school2", [], id="school-with-none-returns-nothing"),
        pytest.param("NON_EXISTENT", [], id="unknown-school-returns-nothing"),
    ],
)
@pytest.mark.asyncio
async def test_get_work_groups_contract(
    work_groups_adapter: Callable[[], Coroutine[Any, Any, WorkGroupsPersistencePort]],
    school: str,
    expected_ids: list[str],
):
    adapter = await work_groups_adapter()
    result = await adapter.get_work_groups(school)
    assert [group.id for group in result] == expected_ids
    # No description upstream, so the display name falls back to the name.
    assert all(group.display_name == group.id for group in result)
    assert all(group.school == school for group in result)
