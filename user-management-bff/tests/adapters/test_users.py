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
from user_management_bff.errors import ObjectNotFoundError, PasswordResetRejectedError
from user_management_bff.models import User, UserAttributes
from user_management_bff.ports import UsersPersistencePort


class TestKelvinUsersPersistenceAdapter:
    @pytest.fixture
    def adapter(self) -> KelvinUsersPersistenceAdapter:
        return KelvinUsersPersistenceAdapter()

    def test_get_settings_cls(self):
        assert KelvinUsersPersistenceAdapter.get_settings_cls() == KelvinPersistenceAdapterSettings

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


@pytest.fixture(params=["file", "kelvin"])
def users_adapter(
    request: pytest.FixtureRequest,
    tmpdir: Path,
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
            async def search(self, *_args: Any, school: str = "", **_kwargs: Any):
                # Kelvin applies ?school= itself, so the adapter is not credited
                # with work the real service does for it.
                for user_data in CONTRACT_USERS:
                    if school in user_data["attributes"]["schools"]:
                        yield make_kelvin_user_from_data(user_data)

            async def get(self, *_args: Any, name: str = "", **_kwargs: Any):
                for user_data in CONTRACT_USERS:
                    if user_data["id"] == name:
                        return make_kelvin_user_from_data(user_data)
                raise NoObject()

        patch_kelvin_resource(user_management_bff.adapters.users, "UserResource", MockUserResource())
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
