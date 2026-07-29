# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import json
import os

import pytest
from ucsschool.kelvin.client import NoObject

import user_management_bff.adapters.users
from user_management_bff.adapters.base import KelvinPersistenceAdapterSettings
from user_management_bff.adapters.users import (
    FileUsersPersistenceAdapter,
    FileUsersPersistenceAdapterSettings,
    KelvinUsersPersistenceAdapter,
)
from user_management_bff.errors import ObjectNotFoundError
from user_management_bff.models import User, UserAttributes


class TestKelvinUsersPersistenceAdapter:
    @pytest.fixture
    def adapter(self):
        return KelvinUsersPersistenceAdapter()

    @pytest.fixture
    def dummy_settings(self):
        return KelvinPersistenceAdapterSettings(
            url="https://test.com", username="test", password="password"
        )

    @pytest.fixture
    def make_kelvin_user_from_data(self, mocker):
        def _make_kelvin_user_from_data(user_data: dict):
            kelvin_user = mocker.MagicMock()
            kelvin_user.name = user_data["id"]
            kelvin_user.lastname = user_data["attributes"]["last_name"]
            kelvin_user.firstname = user_data["attributes"]["first_name"]
            kelvin_user.schools = user_data["attributes"]["schools"]
            kelvin_user.school_classes = user_data["attributes"]["school_classes"]
            kelvin_user.workgroups = user_data["attributes"]["work_groups"]
            kelvin_user.ucsschool_roles = user_data["attributes"]["roles"]
            kelvin_user.disabled = user_data["attributes"]["disabled"]
            kelvin_user.email = user_data["attributes"].get("email", None)
            kelvin_user.birthday = user_data["attributes"].get("birthday", None)
            kelvin_user.expiration_date = user_data["attributes"].get("expiration_date", None)
            return kelvin_user

        return _make_kelvin_user_from_data

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
    def test_user_from_kelvin_user(self, input_data, adapter, make_kelvin_user_from_data):
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
        self, input_data, adapter, make_kelvin_user_from_data
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
        self, adapter, dummy_settings, monkeypatch, mocker, make_kelvin_user_from_data, input_data
    ):
        class MockUserResource:
            async def search(self, *_args, **_kwargs):
                for user_data in input_data:
                    yield make_kelvin_user_from_data(user_data)

        mock_user_resource = mocker.MagicMock(return_value=MockUserResource())
        monkeypatch.setattr(user_management_bff.adapters.users, "UserResource", mock_user_resource)
        await adapter.configure(dummy_settings)
        result = await adapter.get_users("school1", school_classes=None, work_groups=None)
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
        self, adapter, dummy_settings, monkeypatch, mocker, make_kelvin_user_from_data, return_user
    ):
        class MockUserResource:
            async def get(self, *_args, **_kwargs):
                return make_kelvin_user_from_data(return_user)

        mock_user_resource = mocker.MagicMock(return_value=MockUserResource())
        monkeypatch.setattr(user_management_bff.adapters.users, "UserResource", mock_user_resource)
        await adapter.configure(dummy_settings)
        result = await adapter.get_user("test_user1")
        assert result == User(
            id=return_user["id"], attributes=UserAttributes(**return_user["attributes"])
        )

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, adapter, dummy_settings, monkeypatch, mocker):
        class MockUserResource:
            async def get(self, *_args, **_kwargs):
                raise NoObject()

        mock_user_resource = mocker.MagicMock(return_value=MockUserResource())
        monkeypatch.setattr(user_management_bff.adapters.users, "UserResource", mock_user_resource)
        await adapter.configure(dummy_settings)
        with pytest.raises(ObjectNotFoundError, match="Object not found") as exc_info:
            await adapter.get_user("test_user1")
        assert exc_info.value.identifier == "test_user1"


class TestFileUsersPersistenceAdapter:
    @pytest.fixture
    def adapter(self):
        return FileUsersPersistenceAdapter()

    @pytest.fixture
    def users_json(self, tmpdir):
        mock_users_json_path = tmpdir / "users.json"
        disk_users_json_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../data/users.json",
        )
        with open(disk_users_json_path, "r") as disk, open(mock_users_json_path, "w") as mock:
            mock.write(disk.read())
        return mock_users_json_path

    def test_get_settings_cls(self, adapter):
        assert adapter.get_settings_cls() == FileUsersPersistenceAdapterSettings

    @pytest.mark.asyncio
    async def test_configure(self, adapter, tmpdir):
        data_file = tmpdir / "test_data.json"
        data = {"foo": "bar"}
        with open(data_file, "w") as fd:
            json.dump(data, fd)
        await adapter.configure(FileUsersPersistenceAdapterSettings(source=str(data_file)))
        assert adapter._data == data

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
                None,
                None,
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
                None,
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
                None,
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
        self, adapter, school, school_classes, work_groups, expected_users, users_json
    ):
        await adapter.configure(FileUsersPersistenceAdapterSettings(source=users_json))
        result = await adapter.get_users(school, school_classes=school_classes, work_groups=work_groups)
        assert result == [
            User(id=user["id"], attributes=UserAttributes(**user["attributes"]))
            for user in expected_users
        ]

    @pytest.mark.asyncio
    async def test_get_user(self, adapter, users_json):
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
    async def test_get_user_not_found(self, adapter, users_json):
        await adapter.configure(FileUsersPersistenceAdapterSettings(source=users_json))
        with pytest.raises(ObjectNotFoundError, match="Object not found") as exc_info:
            await adapter.get_user("NON_EXISTENT")
        assert exc_info.value.identifier == "NON_EXISTENT"
