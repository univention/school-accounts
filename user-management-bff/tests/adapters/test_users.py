# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import asyncio
import json
import os
from collections.abc import Coroutine
from pathlib import Path
from typing import Any, Callable
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture
from typing_extensions import override
from ucsschool.kelvin.client import InvalidRequest, NoObject

import user_management_bff.adapters.users
from user_management_bff.adapters.base import KelvinPersistenceAdapterSettings
from user_management_bff.adapters.users import (
    FileUsersPersistenceAdapter,
    FileUsersPersistenceAdapterSettings,
    KelvinUsersPersistenceAdapter,
)
from user_management_bff.errors import (
    ObjectNotFoundError,
    PasswordChangeOnNextLoginUnsupportedError,
    PasswordResetRejectedError,
)
from user_management_bff.models import User, UserAttributes
from user_management_bff.ports import UsersPersistencePort


def _contract_shape(username: str) -> dict[str, Any]:
    """The stored-user shape ``make_kelvin_user_from_data`` expects, for one name."""
    return {
        "id": username,
        "attributes": {
            "disabled": False,
            "first_name": "F",
            "last_name": "L",
            "roles": [],
            "schools": [],
            "school_classes": {},
            "work_groups": {},
            "username": username,
        },
    }


class TestKelvinUsersPersistenceAdapter:
    @pytest.fixture
    def adapter(self) -> KelvinUsersPersistenceAdapter:
        return KelvinUsersPersistenceAdapter()

    def test_get_settings_cls(self):
        assert KelvinUsersPersistenceAdapter.get_settings_cls() == KelvinPersistenceAdapterSettings

    @pytest.mark.asyncio
    async def test_set_password_reuses_a_user_the_request_already_read(
        self,
        adapter: KelvinUsersPersistenceAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Resolving the selection already reads every target, and a write needs the
        same object: fetching it again doubled the requests a bulk reset made."""
        await adapter.configure(dummy_settings)
        gets: list[str] = []
        saved: list[tuple[str, str]] = []

        def _kelvin_user(name: str) -> Any:
            user = MagicMock()
            user.name = name
            user.lastname = "L"
            user.firstname = "F"
            user.udm_properties = {}
            user.school_classes = {}
            user.workgroups = {}
            user.ucsschool_roles = []
            user.disabled = False
            user.schools = ["s"]
            user.legal_wards = []
            user.legal_guardians = []
            user.email = None
            user.birthday = None
            user.expiration_date = None

            async def _save() -> None:
                saved.append((name, user.password))

            user.save = _save
            return user

        class _Resource:
            def __init__(self, session: Any = None) -> None:
                pass

            def search(self, school: str) -> Any:
                async def _gen() -> Any:
                    yield _kelvin_user("u1")

                return _gen()

            async def get(self, name: str) -> Any:
                gets.append(name)
                return _kelvin_user(name)

        monkeypatch.setattr(user_management_bff.adapters.users, "UserResource", _Resource)

        await adapter.get_users("s", [], [])
        await adapter.set_password("u1", "new-pw")
        assert saved == [("u1", "new-pw")]
        assert gets == []

        await adapter.set_password("u2", "new-pw")
        assert gets == ["u2"]

    @pytest.mark.parametrize(
        "input_data",
        [
            {
                "attributes": {
                    "disabled": False,
                    "first_name": "firstname",
                    "last_name": "lastname",
                    "roles": ["teacher:school:test_school1"],
                    "schools": ["test_school1"],
                    "school_classes": {"test_school1": ["1a", "2b"]},
                    "username": "test_user1",
                    "work_groups": {"test_school1": ["w1a"]},
                },
                "id": "test_user1",
            }
        ],
    )
    def test_user_from_kelvin_user(
        self,
        input_data: dict[str, Any],
        adapter: KelvinUsersPersistenceAdapter,
        make_kelvin_user_from_data: Callable[[dict[str, Any]], MagicMock],
    ):
        kelvin_user = make_kelvin_user_from_data(input_data)
        result = adapter._user_from_kelvin_user(kelvin_user)
        assert result == User(id=input_data["id"], attributes=UserAttributes(**input_data["attributes"]))

    @pytest.mark.parametrize(
        "input_data",
        [
            {
                "attributes": {
                    "disabled": False,
                    "first_name": "firstname",
                    "last_name": "lastname",
                    "roles": ["staff:school:test_school1"],
                    "schools": ["test_school1"],
                    "school_classes": None,
                    "username": "test_user1",
                    "work_groups": {},
                },
                "id": "test_user1",
            }
        ],
    )
    def test_user_from_kelvin_user_staff_without_classes(
        self,
        input_data: dict[str, Any],
        adapter: KelvinUsersPersistenceAdapter,
        make_kelvin_user_from_data: Callable[[dict[str, Any]], MagicMock],
    ):
        kelvin_user = make_kelvin_user_from_data(input_data)
        result = adapter._user_from_kelvin_user(kelvin_user)
        input_data["attributes"]["school_classes"] = {}
        assert result == User(id=input_data["id"], attributes=UserAttributes(**input_data["attributes"]))

    @pytest.mark.parametrize(
        "input_data",
        [
            [],
            [
                {
                    "attributes": {
                        "disabled": False,
                        "first_name": "firstname",
                        "last_name": "lastname",
                        "roles": ["teacher:school:test_school1"],
                        "schools": ["test_school1"],
                        "school_classes": {"test_school1": ["1a", "2b"]},
                        "work_groups": {},
                        "username": "test_user1",
                    },
                    "id": "test_user1",
                }
            ],
            [
                {
                    "attributes": {
                        "disabled": False,
                        "first_name": "firstname",
                        "last_name": "lastname",
                        "roles": ["teacher:school:test_school1"],
                        "schools": ["test_school1"],
                        "school_classes": {"test_school1": ["1a", "2b"]},
                        "work_groups": {"test_school1": ["w1a"]},
                        "username": "test_user1",
                    },
                    "id": "test_user1",
                },
                {
                    "attributes": {
                        "disabled": False,
                        "first_name": "firstname2",
                        "last_name": "lastname2",
                        "roles": ["teacher:school:test_school2"],
                        "schools": ["test_school2"],
                        "school_classes": {"test_school2": ["1a", "2b"]},
                        "work_groups": {"test_school2": ["w1a"]},
                        "username": "test_user2",
                    },
                    "id": "test_user2",
                },
            ],
        ],
    )
    @pytest.mark.asyncio
    async def test_get_users(
        self,
        adapter: KelvinUsersPersistenceAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
        make_kelvin_user_from_data: Callable[[dict[str, Any]], MagicMock],
        input_data: list[dict[str, Any]],
    ):
        class MockUserResource:
            async def search(self, *_args: Any, **_kwargs: Any):
                for user_data in input_data:
                    yield make_kelvin_user_from_data(user_data)

        mock_user_resource = mocker.MagicMock(return_value=MockUserResource())
        monkeypatch.setattr(user_management_bff.adapters.users, "UserResource", mock_user_resource)
        await adapter.configure(dummy_settings)
        result = await adapter.get_users("school1", school_classes=[], work_groups=[])
        assert result == [
            User(id=user_data["id"], attributes=UserAttributes(**user_data["attributes"]))
            for user_data in input_data
        ]

    @pytest.mark.parametrize(
        "return_user",
        [
            {
                "attributes": {
                    "disabled": False,
                    "first_name": "firstname",
                    "last_name": "lastname",
                    "roles": ["teacher:school:test_school1"],
                    "schools": ["test_school1"],
                    "school_classes": {"test_school1": ["1a", "2b"]},
                    "work_groups": {},
                    "username": "test_user1",
                },
                "id": "test_user1",
            }
        ],
    )
    @pytest.mark.asyncio
    async def test_get_user(
        self,
        adapter: KelvinUsersPersistenceAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
        make_kelvin_user_from_data: Callable[[dict[str, Any]], MagicMock],
        return_user: dict[str, Any],
    ):
        class MockUserResource:
            async def get(self, *_args: Any, **_kwargs: Any):
                return make_kelvin_user_from_data(return_user)

        mock_user_resource = mocker.MagicMock(return_value=MockUserResource())
        monkeypatch.setattr(user_management_bff.adapters.users, "UserResource", mock_user_resource)
        await adapter.configure(dummy_settings)
        result = await adapter.get_user("test_user1")
        assert result == User(
            id=return_user["id"], attributes=UserAttributes(**return_user["attributes"])
        )

    @pytest.mark.asyncio
    async def test_get_user_not_found(
        self,
        adapter: KelvinUsersPersistenceAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
    ):
        class MockUserResource:
            async def get(self, *_args: Any, **_kwargs: Any):
                raise NoObject()

        mock_user_resource = mocker.MagicMock(return_value=MockUserResource())
        monkeypatch.setattr(user_management_bff.adapters.users, "UserResource", mock_user_resource)
        await adapter.configure(dummy_settings)
        with pytest.raises(ObjectNotFoundError, match="Object not found") as exc_info:
            await adapter.get_user("test_user1")
        assert exc_info.value.identifier == "test_user1"

    @pytest.mark.asyncio
    async def test_get_user_reuses_a_user_the_request_already_read(
        self,
        adapter: KelvinUsersPersistenceAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
        make_kelvin_user_from_data: Callable[[dict[str, Any]], MagicMock],
    ):
        """Rendering the list resolves the actor once per section it builds: four
        GETs for one user, none of which the previous one could have been."""
        gets: list[str] = []

        class MockUserResource:
            async def search(self, *_args: Any, name: list[str], **_kwargs: Any):
                for username in name:
                    yield make_kelvin_user_from_data(_contract_shape(username))

            async def get(self, *_args: Any, name: str = "", **_kwargs: Any):
                gets.append(name)
                return make_kelvin_user_from_data(_contract_shape(name))

        monkeypatch.setattr(
            user_management_bff.adapters.users,
            "UserResource",
            mocker.MagicMock(return_value=MockUserResource()),
        )
        await adapter.configure(dummy_settings)
        assert (await adapter.get_user("actor")).id == "actor"
        assert (await adapter.get_user("actor")).id == "actor"
        assert gets == ["actor"]

        # A user the selection search delivered costs nothing either.
        await adapter.get_users_by_id(["u1"])
        assert (await adapter.get_user("u1")).id == "u1"
        assert gets == ["actor"]

    @pytest.mark.asyncio
    async def test_a_group_filter_asks_the_group_who_is_in_it(
        self,
        adapter: KelvinUsersPersistenceAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
        make_kelvin_user_from_data: Callable[[dict[str, Any]], MagicMock],
    ):
        """Kelvin cannot search users by class, so the filtered list used to read
        every user of the school and keep a classroom of them."""
        searches: list[dict[str, Any]] = []

        class MockUserResource:
            async def search(self, *_args: Any, **kwargs: Any):
                searches.append(kwargs)
                for username in kwargs.get("name", []):
                    yield make_kelvin_user_from_data(_contract_shape(username))

        class MockSchoolClassResource:
            async def get(self, *_args: Any, school: str = "", name: str = "", **_kwargs: Any):
                return mocker.MagicMock(users=[f"{school}.{name}.1", f"{school}.{name}.2"])

        monkeypatch.setattr(
            user_management_bff.adapters.users,
            "UserResource",
            mocker.MagicMock(return_value=MockUserResource()),
        )
        monkeypatch.setattr(
            user_management_bff.adapters.users,
            "SchoolClassResource",
            mocker.MagicMock(return_value=MockSchoolClassResource()),
        )
        await adapter.configure(dummy_settings)

        result = await adapter.get_users("school2", school_classes=["1a"], work_groups=[])

        assert [user.id for user in result] == ["school2.1a.1", "school2.1a.2"]
        # The members by name, and never the school.
        assert searches == [{"name": ["school2.1a.1", "school2.1a.2"]}]

    @pytest.mark.asyncio
    async def test_a_group_filter_naming_no_group_lists_nobody(
        self,
        adapter: KelvinUsersPersistenceAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
    ):
        """A filter value outlives the work group it names. The control is rebuilt
        from the same request, so an empty table is the whole answer."""

        class MockWorkGroupResource:
            async def get(self, *_args: Any, **_kwargs: Any):
                raise NoObject()

        monkeypatch.setattr(
            user_management_bff.adapters.users,
            "WorkGroupResource",
            mocker.MagicMock(return_value=MockWorkGroupResource()),
        )
        await adapter.configure(dummy_settings)

        assert await adapter.get_users("school2", school_classes=[], work_groups=["gone"]) == []

    @pytest.mark.asyncio
    async def test_get_users_by_id_asks_for_every_name_in_one_search(
        self,
        adapter: KelvinUsersPersistenceAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
        make_kelvin_user_from_data: Callable[[dict[str, Any]], MagicMock],
    ):
        """A selection is one request, not one per user - that is the whole point."""
        searches: list[list[str]] = []

        class MockUserResource:
            async def search(self, *_args: Any, name: list[str], **_kwargs: Any):
                searches.append(name)
                for username in name:
                    yield make_kelvin_user_from_data(_contract_shape(username))

        monkeypatch.setattr(
            user_management_bff.adapters.users,
            "UserResource",
            mocker.MagicMock(return_value=MockUserResource()),
        )
        await adapter.configure(dummy_settings)
        result = await adapter.get_users_by_id(["u1", "u2", "u3"])
        assert searches == [["u1", "u2", "u3"]]
        assert sorted(result) == ["u1", "u2", "u3"]

    @pytest.mark.asyncio
    async def test_get_users_by_id_splits_a_selection_too_long_for_one_request_line(
        self,
        adapter: KelvinUsersPersistenceAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
        make_kelvin_user_from_data: Callable[[dict[str, Any]], MagicMock],
    ):
        """Past the request-line cap the server answers 414, so the names are split
        over as few requests as still fit - and every user still comes back."""
        searches: list[list[str]] = []

        class MockUserResource:
            async def search(self, *_args: Any, name: list[str], **_kwargs: Any):
                searches.append(name)
                for username in name:
                    yield make_kelvin_user_from_data(_contract_shape(username))

        monkeypatch.setattr(
            user_management_bff.adapters.users,
            "UserResource",
            mocker.MagicMock(return_value=MockUserResource()),
        )
        await adapter.configure(dummy_settings)
        # 12 characters plus "&name=" is 18 bytes, so the budget holds 333 of them.
        names = [f"user{index:08d}" for index in range(700)]
        result = await adapter.get_users_by_id(names)
        assert [len(chunk) for chunk in searches] == [333, 333, 34]
        assert sorted(result) == sorted(names)

    @pytest.mark.asyncio
    async def test_get_users_by_id_does_not_let_a_wildcard_widen_the_search(
        self,
        adapter: KelvinUsersPersistenceAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
        make_kelvin_user_from_data: Callable[[dict[str, Any]], MagicMock],
    ):
        """Kelvin reads `*` in a name as a wildcard. The ids come off a form, and no
        UCS username holds one, so such a value names nobody rather than everybody."""
        searches: list[list[str]] = []

        class MockUserResource:
            async def search(self, *_args: Any, name: list[str], **_kwargs: Any):
                searches.append(name)
                for username in name:
                    yield make_kelvin_user_from_data(_contract_shape(username))

        monkeypatch.setattr(
            user_management_bff.adapters.users,
            "UserResource",
            mocker.MagicMock(return_value=MockUserResource()),
        )
        await adapter.configure(dummy_settings)
        assert await adapter.get_users_by_id(["*"]) == {}
        assert searches == []

    @pytest.mark.asyncio
    async def test_set_password_success(
        self,
        adapter: KelvinUsersPersistenceAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
    ):
        kelvin_user = mocker.MagicMock()
        kelvin_user.save = mocker.AsyncMock(return_value=kelvin_user)

        class MockUserResource:
            async def get(self, *_args: Any, **_kwargs: Any):
                return kelvin_user

        mock_user_resource = mocker.MagicMock(return_value=MockUserResource())
        monkeypatch.setattr(user_management_bff.adapters.users, "UserResource", mock_user_resource)
        await adapter.configure(dummy_settings)
        await adapter.set_password("test_user1", "new-password")
        assert kelvin_user.password == "new-password"
        kelvin_user.save.assert_awaited_once()

    @pytest.mark.parametrize(
        ("configured", "expected"),
        [({"pwdChangeNextLogin": "0", "title": "x"}, True), ({"title": "x"}, False), ({}, False)],
    )
    def test_change_on_next_login_support_is_learned_from_a_fetched_user(
        self,
        adapter: KelvinUsersPersistenceAdapter,
        make_kelvin_user_from_data: Callable[[dict[str, Any]], MagicMock],
        configured: dict[str, str],
        expected: bool,
    ):
        """Kelvin returns exactly its configured allowlist on every user."""
        assert adapter.supports_password_change_on_next_login() is False
        kelvin_user = make_kelvin_user_from_data(
            {
                "id": "test_user1",
                "attributes": {
                    "disabled": False,
                    "first_name": "firstname",
                    "last_name": "lastname",
                    "roles": ["teacher:school:test_school1"],
                    "schools": ["test_school1"],
                    "school_classes": {},
                    "username": "test_user1",
                    "work_groups": {},
                },
            }
        )
        kelvin_user.udm_properties = configured
        adapter._user_from_kelvin_user(kelvin_user)
        assert adapter.supports_password_change_on_next_login() is expected

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("requested", "written"), [(True, True), (False, False)])
    async def test_set_password_only_sends_the_udm_flag_when_it_is_requested(
        self,
        adapter: KelvinUsersPersistenceAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        patch_kelvin_resource: Callable[[Any, str, Any], None],
        mocker: MockerFixture,
        requested: bool,
        written: bool,
    ):
        """An unmapped property makes Kelvin 422 the whole request, password included."""
        kelvin_user = mocker.MagicMock()
        kelvin_user.save = mocker.AsyncMock(return_value=kelvin_user)
        # A typed local: reading the dict back off the MagicMock would be untyped.
        udm_properties: dict[str, object] = {}
        kelvin_user.udm_properties = udm_properties

        class MockUserResource:
            async def get(self, *_args: Any, **_kwargs: Any):
                return kelvin_user

        patch_kelvin_resource(user_management_bff.adapters.users, "UserResource", MockUserResource())
        adapter._change_on_next_login_supported = True
        await adapter.configure(dummy_settings)
        await adapter.set_password("test_user1", "new-password", requested)
        assert kelvin_user.password == "new-password"
        assert udm_properties == ({"pwdChangeNextLogin": True} if written else {})

    @pytest.mark.asyncio
    async def test_set_password_skips_a_user_kelvin_cannot_force_to_change_it(
        self,
        adapter: KelvinUsersPersistenceAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        patch_kelvin_resource: Callable[[Any, str, Any], None],
        mocker: MockerFixture,
        warning_records: list[str],
    ):
        """Half the job - a new password nobody is asked to change - is worse than none."""
        kelvin_user = mocker.MagicMock()
        kelvin_user.save = mocker.AsyncMock(return_value=kelvin_user)
        kelvin_user.udm_properties = {"title": "x", "birthday": "2000-01-01"}

        class MockUserResource:
            async def get(self, *_args: Any, **_kwargs: Any):
                return kelvin_user

        patch_kelvin_resource(user_management_bff.adapters.users, "UserResource", MockUserResource())
        adapter._change_on_next_login_supported = False
        await adapter.configure(dummy_settings)
        with pytest.raises(PasswordChangeOnNextLoginUnsupportedError) as exc_info:
            await adapter.set_password("test_user1", "new-password", True)
        assert exc_info.value.identifier == "test_user1"
        assert kelvin_user.password != "new-password"
        kelvin_user.save.assert_not_awaited()
        assert len(warning_records) == 1
        assert "pwdChangeNextLogin" in warning_records[0]
        assert "birthday,title" in warning_records[0]
        assert "test_user1" in warning_records[0]
        assert "new-password" not in warning_records[0]

    @pytest.mark.asyncio
    async def test_set_password_warns_when_the_password_history_cannot_be_overridden(
        self,
        adapter: KelvinUsersPersistenceAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        patch_kelvin_resource: Callable[[Any, str, Any], None],
        mocker: MockerFixture,
        warning_records: list[str],
    ):
        """The reset still runs; only a reused password is refused, and that refusal leaks."""
        kelvin_user = mocker.MagicMock()
        kelvin_user.save = mocker.AsyncMock(return_value=kelvin_user)
        kelvin_user.udm_properties = {"title": "x", "birthday": "2000-01-01"}

        class MockUserResource:
            async def get(self, *_args: Any, **_kwargs: Any):
                return kelvin_user

        patch_kelvin_resource(user_management_bff.adapters.users, "UserResource", MockUserResource())
        await adapter.configure(dummy_settings)
        await adapter.set_password("test_user1", "new-password")
        assert kelvin_user.password == "new-password"
        kelvin_user.save.assert_awaited_once()
        assert len(warning_records) == 1
        assert "overridePWHistory" in warning_records[0]
        assert "birthday,title" in warning_records[0]
        assert "test_user1" in warning_records[0]
        assert "new-password" not in warning_records[0]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("mapped", "expected"),
        [({"overridePWHistory": "0"}, {"overridePWHistory": True}), ({}, {})],
    )
    async def test_set_password_overrides_the_password_history_when_kelvin_maps_it(
        self,
        adapter: KelvinUsersPersistenceAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
        mapped: dict[str, object],
        expected: dict[str, object],
    ):
        """Refusing a reused password would tell the teacher what this student once used."""
        kelvin_user = mocker.MagicMock()
        kelvin_user.save = mocker.AsyncMock(return_value=kelvin_user)
        udm_properties: dict[str, object] = dict(mapped)
        kelvin_user.udm_properties = udm_properties

        class MockUserResource:
            async def get(self, *_args: Any, **_kwargs: Any):
                return kelvin_user

        monkeypatch.setattr(
            user_management_bff.adapters.users,
            "UserResource",
            mocker.MagicMock(return_value=MockUserResource()),
        )
        await adapter.configure(dummy_settings)
        await adapter.set_password("test_user1", "new-password")
        assert udm_properties == expected

    @pytest.mark.asyncio
    async def test_set_password_not_found(
        self,
        adapter: KelvinUsersPersistenceAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
    ):
        class MockUserResource:
            async def get(self, *_args: Any, **_kwargs: Any):
                raise NoObject()

        mock_user_resource = mocker.MagicMock(return_value=MockUserResource())
        monkeypatch.setattr(user_management_bff.adapters.users, "UserResource", mock_user_resource)
        await adapter.configure(dummy_settings)
        with pytest.raises(ObjectNotFoundError, match="Object not found") as exc_info:
            await adapter.set_password("test_user1", "new-password")
        assert exc_info.value.identifier == "test_user1"

    @pytest.mark.asyncio
    async def test_set_password_rejected(
        self,
        adapter: KelvinUsersPersistenceAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
    ):
        kelvin_user = mocker.MagicMock()
        kelvin_user.save = mocker.AsyncMock(side_effect=InvalidRequest(reason="policy violation"))

        class MockUserResource:
            async def get(self, *_args: Any, **_kwargs: Any):
                return kelvin_user

        mock_user_resource = mocker.MagicMock(return_value=MockUserResource())
        monkeypatch.setattr(user_management_bff.adapters.users, "UserResource", mock_user_resource)
        await adapter.configure(dummy_settings)
        with pytest.raises(PasswordResetRejectedError) as exc_info:
            await adapter.set_password("test_user1", "new-password")
        assert exc_info.value.identifier == "test_user1"
        assert exc_info.value.message == "policy violation"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("raw_reason", "expected"),
        [
            ([{"loc": ["body", "password"], "msg": "bad", "type": "UdmError"}], "bad"),
            ([{"msg": "first"}, {"msg": "second"}], "first second"),
            ({"detail": "something else"}, "{'detail': 'something else'}"),
        ],
    )
    async def test_set_password_rejected_reports_only_the_udm_msg(
        self,
        adapter: KelvinUsersPersistenceAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
        raw_reason: object,
        expected: str,
    ):
        # InvalidRequest's own stub types `reason` as `str`, but it's really just
        # `resp_json["detail"]` off the wire - untyped at the source, so a shape like
        # this is a real possibility the stub doesn't capture.
        kelvin_user = mocker.MagicMock()
        kelvin_user.save = mocker.AsyncMock(
            side_effect=InvalidRequest(reason=raw_reason)  # pyright: ignore[reportArgumentType]
        )

        class MockUserResource:
            async def get(self, *_args: Any, **_kwargs: Any):
                return kelvin_user

        mock_user_resource = mocker.MagicMock(return_value=MockUserResource())
        monkeypatch.setattr(user_management_bff.adapters.users, "UserResource", mock_user_resource)
        await adapter.configure(dummy_settings)
        with pytest.raises(PasswordResetRejectedError) as exc_info:
            await adapter.set_password("test_user1", "new-password")
        assert exc_info.value.message == expected

    @pytest.mark.asyncio
    async def test_set_password_rejected_falls_back_to_empty_reason_if_str_raises(
        self,
        adapter: KelvinUsersPersistenceAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
    ):
        class _Unstringifiable:
            @override
            def __str__(self) -> str:
                raise RuntimeError("cannot stringify")

        kelvin_user = mocker.MagicMock()
        kelvin_user.save = mocker.AsyncMock(
            side_effect=InvalidRequest(
                reason=_Unstringifiable()  # pyright: ignore[reportArgumentType]
            )
        )

        class MockUserResource:
            async def get(self, *_args: Any, **_kwargs: Any):
                return kelvin_user

        mock_user_resource = mocker.MagicMock(return_value=MockUserResource())
        monkeypatch.setattr(user_management_bff.adapters.users, "UserResource", mock_user_resource)
        await adapter.configure(dummy_settings)
        with pytest.raises(PasswordResetRejectedError) as exc_info:
            await adapter.set_password("test_user1", "new-password")
        assert exc_info.value.message == ""


class TestFileUsersPersistenceAdapter:
    @pytest.fixture
    def adapter(self) -> FileUsersPersistenceAdapter:
        return FileUsersPersistenceAdapter()

    @pytest.fixture
    def users_json(self, tmpdir: Path) -> Any:
        mock_users_json_path = tmpdir / "users.json"
        disk_users_json_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../data/users.json",
        )
        with open(disk_users_json_path, "r") as disk, open(mock_users_json_path, "w") as mock:
            mock.write(disk.read())
        return mock_users_json_path

    def test_get_settings_cls(self, adapter: FileUsersPersistenceAdapter):
        assert adapter.get_settings_cls() == FileUsersPersistenceAdapterSettings

    @pytest.mark.asyncio
    async def test_configure(self, adapter: FileUsersPersistenceAdapter, tmpdir: Path):
        # The whole file is validated on load, so this needs a valid user record.
        data_file = tmpdir / "test_data.json"
        data: list[dict[str, Any]] = [
            {
                "attributes": {
                    "disabled": False,
                    "first_name": "firstname",
                    "last_name": "lastname",
                    "roles": ["teacher:school:test_school1"],
                    "schools": ["test_school1"],
                    "school_classes": {"test_school1": ["1a"]},
                    "username": "firstname.lastname",
                    "work_groups": {},
                },
                "id": "test_user1",
            }
        ]
        with open(data_file, "w") as fd:
            json.dump(data, fd)
        await adapter.configure(FileUsersPersistenceAdapterSettings(source=str(data_file)))
        assert adapter._data == [
            User(id=user["id"], attributes=UserAttributes(**user["attributes"])) for user in data
        ]

    @pytest.mark.parametrize(
        "school,school_classes,work_groups,expected_users",
        [
            ("NON_EXISTENT", [], [], []),
            (
                "test_school1",
                [],
                [],
                [
                    {
                        "attributes": {
                            "disabled": False,
                            "first_name": "firstname",
                            "last_name": "lastname",
                            "roles": ["teacher:school:test_school1"],
                            "schools": ["test_school1"],
                            "school_classes": {"test_school1": ["1a", "2b"]},
                            "username": "firstname.lastname",
                            "work_groups": {},
                        },
                        "id": "test_user1",
                    },
                    {
                        "attributes": {
                            "disabled": False,
                            "first_name": "firstname4",
                            "last_name": "lastname4",
                            "roles": ["school_admin:school:test_school1"],
                            "school_classes": {"test_school1": ["1a"]},
                            "schools": ["test_school1"],
                            "username": "firstname4.lastname4",
                            "work_groups": {},
                        },
                        "id": "test_user4",
                    },
                ],
            ),
            (
                "test_school2",
                [],
                [],
                [
                    {
                        "attributes": {
                            "disabled": False,
                            "first_name": "firstname2",
                            "last_name": "lastname2",
                            "roles": ["teacher:school:test_school2"],
                            "schools": ["test_school2"],
                            "school_classes": {"test_school2": ["1a", "2b"]},
                            "username": "firstname2.lastname2",
                            "work_groups": {"test_school2": ["w1a"]},
                        },
                        "id": "test_user2",
                    },
                    {
                        "attributes": {
                            "disabled": False,
                            "first_name": "firstname3",
                            "last_name": "lastname3",
                            "roles": [
                                "teacher:school:test_school2",
                                "student:school:test_school3",
                            ],
                            "schools": ["test_school2", "test_school3"],
                            "school_classes": {"test_school1": ["1a", "2b"], "test_school2": ["3c"]},
                            "username": "firstname3.lastname3",
                            "work_groups": {},
                        },
                        "id": "test_user3",
                    },
                ],
            ),
            (
                "test_school2",
                [],
                [],
                [
                    {
                        "attributes": {
                            "disabled": False,
                            "first_name": "firstname2",
                            "last_name": "lastname2",
                            "roles": ["teacher:school:test_school2"],
                            "schools": ["test_school2"],
                            "school_classes": {"test_school2": ["1a", "2b"]},
                            "username": "firstname2.lastname2",
                            "work_groups": {"test_school2": ["w1a"]},
                        },
                        "id": "test_user2",
                    },
                    {
                        "attributes": {
                            "disabled": False,
                            "first_name": "firstname3",
                            "last_name": "lastname3",
                            "roles": [
                                "teacher:school:test_school2",
                                "student:school:test_school3",
                            ],
                            "schools": ["test_school2", "test_school3"],
                            "school_classes": {"test_school1": ["1a", "2b"], "test_school2": ["3c"]},
                            "username": "firstname3.lastname3",
                            "work_groups": {},
                        },
                        "id": "test_user3",
                    },
                ],
            ),
            (
                "test_school2",
                ["3c"],
                [],
                [
                    {
                        "attributes": {
                            "disabled": False,
                            "first_name": "firstname3",
                            "last_name": "lastname3",
                            "roles": [
                                "teacher:school:test_school2",
                                "student:school:test_school3",
                            ],
                            "schools": ["test_school2", "test_school3"],
                            "school_classes": {"test_school1": ["1a", "2b"], "test_school2": ["3c"]},
                            "username": "firstname3.lastname3",
                            "work_groups": {},
                        },
                        "id": "test_user3",
                    },
                ],
            ),
            (
                "test_school2",
                [],
                ["w1a"],
                [
                    {
                        "attributes": {
                            "disabled": False,
                            "first_name": "firstname2",
                            "last_name": "lastname2",
                            "roles": ["teacher:school:test_school2"],
                            "schools": ["test_school2"],
                            "school_classes": {"test_school2": ["1a", "2b"]},
                            "username": "firstname2.lastname2",
                            "work_groups": {"test_school2": ["w1a"]},
                        },
                        "id": "test_user2",
                    },
                ],
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_get_users_with_search_filters(
        self,
        adapter: FileUsersPersistenceAdapter,
        school: str,
        school_classes: list[str],
        work_groups: list[str],
        expected_users: list[dict[str, Any]],
        users_json: Any,
    ):
        await adapter.configure(FileUsersPersistenceAdapterSettings(source=users_json))
        result = await adapter.get_users(school, school_classes=school_classes, work_groups=work_groups)
        assert result == [
            User(id=user["id"], attributes=UserAttributes(**user["attributes"]))
            for user in expected_users
        ]

    @pytest.mark.asyncio
    async def test_get_user(self, adapter: FileUsersPersistenceAdapter, users_json: Any):
        await adapter.configure(FileUsersPersistenceAdapterSettings(source=users_json))
        result = await adapter.get_user("dev")
        assert result == User(
            id="dev",
            attributes=UserAttributes(
                last_name="User",
                first_name="Dev",
                username="dev",
                disabled=False,
                schools=["school1"],
                school_classes={"school1": ["1a", "2b"]},
                work_groups={},
                roles=["teacher:school:school1"],
            ),
        )

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, adapter: FileUsersPersistenceAdapter, users_json: Any):
        await adapter.configure(FileUsersPersistenceAdapterSettings(source=users_json))
        with pytest.raises(ObjectNotFoundError, match="Object not found") as exc_info:
            await adapter.get_user("NON_EXISTENT")
        assert exc_info.value.identifier == "NON_EXISTENT"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("requested", [True, False])
    async def test_set_password_stores_change_on_next_login(
        self, adapter: FileUsersPersistenceAdapter, users_json: Any, requested: bool
    ):
        await adapter.configure(FileUsersPersistenceAdapterSettings(source=users_json))
        await adapter.set_password("dev", "new-password", requested)
        stored = next(u for u in json.load(open(users_json)) if u["id"] == "dev")
        assert stored["attributes"]["change_password_on_next_login"] is requested

    @pytest.mark.asyncio
    async def test_set_password_success(self, adapter: FileUsersPersistenceAdapter, users_json: Any):
        await adapter.configure(FileUsersPersistenceAdapterSettings(source=users_json))
        stored_before = len(json.load(open(users_json)))
        await adapter.set_password("dev", "new-password")
        result = await adapter.get_user("dev")
        assert result == User(
            id="dev",
            attributes=UserAttributes(
                last_name="User",
                first_name="Dev",
                username="dev",
                disabled=False,
                schools=["school1"],
                school_classes={"school1": ["1a", "2b"]},
                work_groups={},
                roles=["teacher:school:school1"],
                password="new-password",
            ),
        )
        # set_password rewrites the whole store through dump_json, so every other
        # record has to survive the write, not just the one that changed.
        assert len(json.load(open(users_json))) == stored_before

    @pytest.mark.asyncio
    async def test_concurrent_set_password_keeps_the_store_readable(
        self, adapter: FileUsersPersistenceAdapter, users_json: Any
    ):
        """A bulk reset writes concurrently. Opening "wb" truncates the file, so
        without serialising the read-modify-write another coroutine read it empty
        and the whole request died on `Invalid JSON: EOF while parsing`."""
        await adapter.configure(FileUsersPersistenceAdapterSettings(source=users_json))
        identifiers = [user.id for user in adapter._data]
        assert len(identifiers) > 1

        await asyncio.gather(*(adapter.set_password(uid, "concurrent-pw") for uid in identifiers))

        stored = {user["id"]: user["attributes"].get("password") for user in json.load(open(users_json))}
        assert stored == {uid: "concurrent-pw" for uid in identifiers}

    @pytest.mark.asyncio
    async def test_set_password_not_found(self, adapter: FileUsersPersistenceAdapter, users_json: Any):
        await adapter.configure(FileUsersPersistenceAdapterSettings(source=users_json))
        with pytest.raises(ObjectNotFoundError, match="Object not found") as exc_info:
            await adapter.set_password("NON_EXISTENT", "new-password")
        assert exc_info.value.identifier == "NON_EXISTENT"


# ---------------------------------------------------------------------------
# UsersPersistencePort contract: one matrix, run against every implementation.
#
# It speaks only the port's own signature -- plain lists -- so an empty list is
# the only way to say "no group filter". That is the exact call issue #230 got
# wrong, and it is unrepresentable in the adapters' own test classes above as
# long as those keep passing whatever each implementation happens to tolerate.
# ---------------------------------------------------------------------------

CONTRACT_SCHOOL = "school1"

CONTRACT_USERS: list[dict[str, Any]] = [
    {
        "id": "student.aiko",
        "attributes": {
            "disabled": False,
            "first_name": "Aiko",
            "last_name": "Tan",
            "roles": ["student:school:school1"],
            "schools": ["school1"],
            "school_classes": {"school1": ["1a"]},
            "work_groups": {"school1": ["w1"]},
            "username": "student.aiko",
        },
    },
    {
        "id": "student.bruno",
        "attributes": {
            "disabled": False,
            "first_name": "Bruno",
            "last_name": "Alves",
            "roles": ["student:school:school1"],
            "schools": ["school1"],
            "school_classes": {"school1": ["1b"]},
            "work_groups": {},
            "username": "student.bruno",
        },
    },
    {
        # A school member with no classes at all -- normal for staff, and the
        # case that used to raise KeyError in the file adapter.
        "id": "staff.novak",
        "attributes": {
            "disabled": False,
            "first_name": "Novak",
            "last_name": "Kraus",
            "roles": ["staff:school:school1"],
            "schools": ["school1"],
            "school_classes": {},
            "work_groups": {},
            "username": "staff.novak",
        },
    },
    {
        # Another school reusing the same class and work group names, so a
        # filter that ignores the school boundary is caught.
        "id": "student.carla",
        "attributes": {
            "disabled": False,
            "first_name": "Carla",
            "last_name": "Moser",
            "roles": ["student:school:school2"],
            "schools": ["school2"],
            "school_classes": {"school2": ["1a"]},
            "work_groups": {"school2": ["w1"]},
            "username": "student.carla",
        },
    },
]

EVERYONE_IN_CONTRACT_SCHOOL = ["staff.novak", "student.aiko", "student.bruno"]


def _contract_group_members(kind: str, school: str, name: str) -> list[str]:
    """Who CONTRACT_USERS says is in one group, read from the group's side."""
    return [
        user_data["id"]
        for user_data in CONTRACT_USERS
        if name in user_data["attributes"][kind].get(school, [])
    ]


def _contract_group_names(kind: str) -> set[tuple[str, str]]:
    """Every (school, name) any contract user is in, so an unknown one can 404."""
    return {
        (school, name)
        for user_data in CONTRACT_USERS
        for school, names in user_data["attributes"][kind].items()
        for name in names
    }


@pytest.fixture(params=["file", "kelvin"])
def users_adapter(
    request: pytest.FixtureRequest,
    tmpdir: Path,
    mocker: MockerFixture,
    dummy_settings: KelvinPersistenceAdapterSettings,
    patch_kelvin_resource: Callable[[Any, str, Any], None],
    make_kelvin_user_from_data: Callable[[dict[str, Any]], MagicMock],
) -> Callable[[], Coroutine[Any, Any, UsersPersistencePort]]:
    """Configure one implementation of UsersPersistencePort over CONTRACT_USERS."""

    async def _file() -> UsersPersistencePort:
        source = tmpdir / "contract_users.json"
        with open(source, "w") as fd:
            json.dump(CONTRACT_USERS, fd)
        adapter = FileUsersPersistenceAdapter()
        await adapter.configure(FileUsersPersistenceAdapterSettings(source=str(source)))
        return adapter

    async def _kelvin() -> UsersPersistencePort:
        class MockUserResource:
            async def search(
                self, *_args: Any, school: str = "", name: list[str] | None = None, **_kwargs: Any
            ):
                # Kelvin applies ?school= and ?name= itself, so the adapter is not
                # credited with work the real service does for it.
                for user_data in CONTRACT_USERS:
                    if name is not None and user_data["id"] not in name:
                        continue
                    if school and school not in user_data["attributes"]["schools"]:
                        continue
                    yield make_kelvin_user_from_data(user_data)

            async def get(self, *_args: Any, name: str = "", **_kwargs: Any):
                for user_data in CONTRACT_USERS:
                    if user_data["id"] == name:
                        return make_kelvin_user_from_data(user_data)
                raise NoObject()

        class MockGroupResource:
            """A class or work group, which Kelvin answers with its member list."""

            _kind: str

            def __init__(self, kind: str):
                self._kind = kind

            async def get(self, *_args: Any, school: str = "", name: str = "", **_kwargs: Any):
                if (school, name) not in _contract_group_names(self._kind):
                    raise NoObject()
                return mocker.MagicMock(users=_contract_group_members(self._kind, school, name))

        patch_kelvin_resource(user_management_bff.adapters.users, "UserResource", MockUserResource())
        patch_kelvin_resource(
            user_management_bff.adapters.users,
            "SchoolClassResource",
            MockGroupResource("school_classes"),
        )
        patch_kelvin_resource(
            user_management_bff.adapters.users, "WorkGroupResource", MockGroupResource("work_groups")
        )
        adapter = KelvinUsersPersistenceAdapter()
        await adapter.configure(dummy_settings)
        return adapter

    return _file if request.param == "file" else _kelvin


@pytest.mark.parametrize(
    "school_classes,work_groups,expected_ids",
    [
        pytest.param([], [], EVERYONE_IN_CONTRACT_SCHOOL, id="empty-lists-keep-everyone"),
        pytest.param(["1a"], [], ["student.aiko"], id="by-school-class"),
        pytest.param(["1b"], [], ["student.bruno"], id="by-other-school-class"),
        pytest.param([], ["w1"], ["student.aiko"], id="by-work-group"),
        pytest.param(["1b"], ["w1"], ["student.aiko", "student.bruno"], id="class-or-work-group"),
        pytest.param(["9z"], ["w9"], [], id="no-match"),
    ],
)
@pytest.mark.asyncio
async def test_get_users_group_filter_contract(
    users_adapter: Callable[[], Coroutine[Any, Any, UsersPersistencePort]],
    school_classes: list[str],
    work_groups: list[str],
    expected_ids: list[str],
):
    adapter = await users_adapter()
    result = await adapter.get_users(
        CONTRACT_SCHOOL, school_classes=school_classes, work_groups=work_groups
    )
    assert sorted(user.id for user in result) == expected_ids


@pytest.mark.asyncio
async def test_get_users_unknown_school_contract(
    users_adapter: Callable[[], Coroutine[Any, Any, UsersPersistencePort]],
):
    adapter = await users_adapter()
    assert await adapter.get_users("NON_EXISTENT", school_classes=[], work_groups=[]) == []


@pytest.mark.asyncio
async def test_get_user_contract(
    users_adapter: Callable[[], Coroutine[Any, Any, UsersPersistencePort]],
):
    adapter = await users_adapter()
    assert await adapter.get_user("staff.novak") == User(
        id="staff.novak", attributes=UserAttributes(**CONTRACT_USERS[2]["attributes"])
    )


@pytest.mark.asyncio
async def test_get_user_unknown_contract(
    users_adapter: Callable[[], Coroutine[Any, Any, UsersPersistencePort]],
):
    adapter = await users_adapter()
    with pytest.raises(ObjectNotFoundError) as exc_info:
        await adapter.get_user("NON_EXISTENT")
    assert exc_info.value.identifier == "NON_EXISTENT"


@pytest.mark.asyncio
async def test_get_users_by_id_contract(
    users_adapter: Callable[[], Coroutine[Any, Any, UsersPersistencePort]],
):
    """Every id the backend knows comes back, keyed by id, across schools."""
    adapter = await users_adapter()
    result = await adapter.get_users_by_id(["staff.novak", "student.carla"])
    assert sorted(result) == ["staff.novak", "student.carla"]
    assert result["staff.novak"] == User(
        id="staff.novak", attributes=UserAttributes(**CONTRACT_USERS[2]["attributes"])
    )


@pytest.mark.asyncio
async def test_get_users_by_id_skips_unknown_ids_contract(
    users_adapter: Callable[[], Coroutine[Any, Any, UsersPersistencePort]],
):
    """An id nobody answers to is absent rather than raising: the caller compares
    against what it asked for and reports the difference as ``not_found``."""
    adapter = await users_adapter()
    result = await adapter.get_users_by_id(["staff.novak", "NON_EXISTENT"])
    assert sorted(result) == ["staff.novak"]


@pytest.mark.asyncio
async def test_get_users_by_id_without_ids_contract(
    users_adapter: Callable[[], Coroutine[Any, Any, UsersPersistencePort]],
):
    adapter = await users_adapter()
    assert await adapter.get_users_by_id([]) == {}
