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

import ucsschool_accounts.adapters.school_classes
from ucsschool_accounts.adapters.base import KelvinPersistenceAdapterSettings
from ucsschool_accounts.adapters.school_classes import (
    FileSchoolClassesPersistenceAdapter,
    FileSchoolClassesPersistenceAdapterSettings,
    KelvinSchoolClassesPersistenceAdapter,
)
from ucsschool_accounts.models import SchoolClass
from ucsschool_accounts.ports import SchoolClassesPersistencePort


class TestKelvinSchoolClassesPersistenceAdapter:
    @pytest.fixture
    def adapter(self) -> KelvinSchoolClassesPersistenceAdapter:
        return KelvinSchoolClassesPersistenceAdapter()

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
            ucsschool_accounts.adapters.school_classes, "SchoolClassResource", mock_school_resource
        )
        await adapter.configure(dummy_settings)
        result = await adapter.get_school_classes("school1")
        assert result == [
            SchoolClass(id=school_data["id"], display_name=school_data["display_name"], school="school1")
            for school_data in input_data
        ]

    @pytest.mark.asyncio
    async def test_get_school_classes_by_name_without_names_never_calls_kelvin(
        self,
        adapter: KelvinSchoolClassesPersistenceAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
    ):
        """No names, no request - not even a token: the port promises no I/O here."""
        resource = mocker.MagicMock()
        monkeypatch.setattr(
            ucsschool_accounts.adapters.school_classes, "SchoolClassResource", resource
        )
        await adapter.configure(dummy_settings)
        assert await adapter.get_school_classes_by_name("school1", []) == []
        resource.assert_not_called()

    @pytest.mark.asyncio
    async def test_names_are_asked_for_in_one_search(
        self,
        adapter: KelvinSchoolClassesPersistenceAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        monkeypatch: pytest.MonkeyPatch,
        make_kelvin_school_from_data: Callable[[dict[str, str]], MagicMock],
    ):
        """Resolving the groups of a user list is a request per school, not per group."""
        searched: list[list[str]] = []

        class _Resource:
            def __init__(self, session: Any = None) -> None:
                pass

            def search(self, school: str, name: list[str], exclude: str) -> Any:
                searched.append(name)

                async def _gen() -> Any:
                    for wanted in name:
                        yield make_kelvin_school_from_data(
                            {"id": wanted, "display_name": wanted.upper()}
                        )

                return _gen()

        monkeypatch.setattr(
            ucsschool_accounts.adapters.school_classes, "SchoolClassResource", _Resource
        )
        await adapter.configure(dummy_settings)

        result = await adapter.get_school_classes_by_name("school1", ["1a", "2b"])

        assert [school_class.id for school_class in result] == ["1a", "2b"]
        assert searched == [["1a", "2b"]]

    @pytest.mark.asyncio
    async def test_a_wildcard_name_is_never_asked_for(
        self,
        adapter: KelvinSchoolClassesPersistenceAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
    ):
        """Kelvin reads ``*`` as a wildcard, so such a value would widen the search
        rather than name a group - and nothing is left to ask for."""
        resource = mocker.MagicMock()
        monkeypatch.setattr(
            ucsschool_accounts.adapters.school_classes, "SchoolClassResource", resource
        )
        await adapter.configure(dummy_settings)

        assert await adapter.get_school_classes_by_name("school1", ["*"]) == []

    @pytest.mark.asyncio
    @pytest.mark.parametrize("read", ["whole school", "by name"])
    async def test_a_listing_leaves_the_members_out(
        self,
        adapter: KelvinSchoolClassesPersistenceAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        patch_kelvin_resource: Callable[[Any, str, Any], None],
        make_kelvin_group_from_data: Callable[[str, str | None], MagicMock],
        read: str,
    ):
        """The members are most of what a group listing costs Kelvin, and all the
        adapter keeps of a group is its name and description."""
        asked: list[dict[str, Any]] = []

        class _Resource:
            async def search(self, **kwargs: Any):
                asked.append(kwargs)
                yield make_kelvin_group_from_data("1a", None)

        patch_kelvin_resource(
            ucsschool_accounts.adapters.school_classes, "SchoolClassResource", _Resource()
        )
        await adapter.configure(dummy_settings)
        if read == "whole school":
            await adapter.get_school_classes("school1")
        else:
            await adapter.get_school_classes_by_name("school1", ["1a"])

        assert [kwargs["exclude"] for kwargs in asked] == ["users"]


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


# ---------------------------------------------------------------------------
# SchoolClassesPersistencePort contract: one matrix, run against every implementation.
#
# The file format is {school: [name, ...]} with nowhere to put a description,
# so the dataset gives the Kelvin fake description=None and the contract asserts
# the display-name fallback both adapters implement. The description-present case
# stays in the Kelvin-only test above.
# ---------------------------------------------------------------------------

CONTRACT_SCHOOL_CLASSES: dict[str, list[str]] = {
    "school1": ["1a", "2b"],
    # A school that has none at all -- the case the file adapter used to raise
    # KeyError on, while the Kelvin adapter returned an empty list.
    "school2": [],
}


@pytest.fixture(params=["file", "kelvin"])
def school_classes_adapter(
    request: pytest.FixtureRequest,
    tmpdir: Path,
    dummy_settings: KelvinPersistenceAdapterSettings,
    patch_kelvin_resource: Callable[[Any, str, Any], None],
    make_kelvin_group_from_data: Callable[[str, str | None], MagicMock],
) -> Callable[[], Coroutine[Any, Any, SchoolClassesPersistencePort]]:
    """Configure one implementation of SchoolClassesPersistencePort over CONTRACT_SCHOOL_CLASSES."""

    async def _file() -> SchoolClassesPersistencePort:
        source = tmpdir / "contract_school_classes.json"
        with open(source, "w") as fd:
            json.dump(CONTRACT_SCHOOL_CLASSES, fd)
        adapter = FileSchoolClassesPersistenceAdapter()
        await adapter.configure(FileSchoolClassesPersistenceAdapterSettings(source=str(source)))
        return adapter

    async def _kelvin() -> SchoolClassesPersistencePort:
        class MockResource:
            async def search(self, *_args: Any, school: str = "", **_kwargs: Any):
                # Kelvin applies ?school= itself, so the adapter is not credited
                # with work the real service does for it.
                for name in CONTRACT_SCHOOL_CLASSES.get(school, []):
                    yield make_kelvin_group_from_data(name, None)

        patch_kelvin_resource(
            ucsschool_accounts.adapters.school_classes, "SchoolClassResource", MockResource()
        )
        adapter = KelvinSchoolClassesPersistenceAdapter()
        await adapter.configure(dummy_settings)
        return adapter

    return _file if request.param == "file" else _kelvin


@pytest.mark.parametrize(
    "school,expected_ids",
    [
        pytest.param("school1", ["1a", "2b"], id="returns-every-group-of-the-school"),
        pytest.param("school2", [], id="school-with-none-returns-nothing"),
        pytest.param("NON_EXISTENT", [], id="unknown-school-returns-nothing"),
    ],
)
@pytest.mark.asyncio
async def test_get_school_classes_contract(
    school_classes_adapter: Callable[[], Coroutine[Any, Any, SchoolClassesPersistencePort]],
    school: str,
    expected_ids: list[str],
):
    adapter = await school_classes_adapter()
    result = await adapter.get_school_classes(school)
    assert [group.id for group in result] == expected_ids
    # No description upstream, so the display name falls back to the name.
    assert all(group.display_name == group.id for group in result)
    assert all(group.school == school for group in result)


@pytest.mark.parametrize(
    "school,names,expected_ids",
    [
        pytest.param("school1", ["1a", "2b"], ["1a", "2b"], id="returns-the-named-groups"),
        pytest.param("school1", ["2b"], ["2b"], id="returns-only-what-was-asked-for"),
        pytest.param("school1", ["2b", "1a"], ["2b", "1a"], id="keeps-the-order-asked-for"),
        # A group deleted between reading the user that references it and this
        # lookup must not take the whole list down with it.
        pytest.param("school1", ["1a", "GONE"], ["1a"], id="skips-an-unknown-name"),
        pytest.param("school1", [], [], id="no-names-returns-nothing"),
        pytest.param("school2", ["1a"], [], id="school-with-none-returns-nothing"),
        pytest.param("NON_EXISTENT", ["1a"], [], id="unknown-school-returns-nothing"),
    ],
)
@pytest.mark.asyncio
async def test_get_school_classes_by_name_contract(
    school_classes_adapter: Callable[[], Coroutine[Any, Any, SchoolClassesPersistencePort]],
    school: str,
    names: list[str],
    expected_ids: list[str],
):
    adapter = await school_classes_adapter()
    result = await adapter.get_school_classes_by_name(school, names)
    assert [group.id for group in result] == expected_ids
    assert all(group.display_name == group.id for group in result)
    assert all(group.school == school for group in result)
