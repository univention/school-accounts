# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import json
import os
from unittest.mock import patch

import pytest
from ucsschool.kelvin.client import NoObject
from ucsschool.kelvin.client import User as KelvinUser

import user_management_bff.adapters.users
from user_management_bff.adapters.base import KelvinPersistenceAdapterSettings
from user_management_bff.adapters.users import (
    FileUsersPersistenceAdapter,
    FileUsersPersistenceAdapterSettings,
    KelvinUsersPersistenceAdapter,
)
from user_management_bff.errors import CreationError, ObjectNotFoundError
from user_management_bff.models import User, UserAttributes, UserCreateRequest


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
            kelvin_user.ucsschool_roles = user_data["attributes"]["roles"]
            kelvin_user.disabled = user_data["attributes"]["disabled"]
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
        result = await adapter.get_users("school1")
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
        with pytest.raises(ObjectNotFoundError, match="Object not found: test_user1") as exc_info:
            await adapter.get_user("test_user1")
        assert exc_info.value.identifier == "test_user1"

    @patch.object(KelvinUser, "save", return_value=None)
    @pytest.mark.asyncio
    async def test_create_user(self, mock_save, adapter, dummy_settings):
        await adapter.configure(dummy_settings)
        result = await adapter.create_user(
            UserCreateRequest(
                first_name="firstname",
                last_name="lastname",
                username="test_user1",
                disabled=False,
                schools=["school1"],
                school_classes={"school1": ["1a", "2b"]},
                roles=["teacher"],
                password="univention",
            )
        )
        await mock_save.called_once()
        assert result == User(
            id="test_user1",
            attributes=UserAttributes(
                last_name="lastname",
                first_name="firstname",
                username="test_user1",
                disabled=False,
                schools=["school1"],
                school_classes={"school1": ["1a", "2b"]},
                roles=["teacher"],
                password=None,
            ),
        )

    @patch.object(KelvinUser, "save", side_effect=NoObject("error"))
    @pytest.mark.asyncio
    async def test_create_user_error(self, mock_save, adapter, dummy_settings):
        await adapter.configure(dummy_settings)
        with pytest.raises(CreationError) as exc_info:
            await adapter.create_user(
                UserCreateRequest(
                    first_name="firstname",
                    last_name="lastname",
                    username="test_user1",
                    disabled=False,
                    schools=["school1"],
                    school_classes={"school1": ["1a", "2b"]},
                    roles=["teacher"],
                    password="univention",
                )
            )
        await mock_save.called_once()
        assert exc_info.value.message == "error"

    @pytest.mark.asyncio
    async def test_delete_user(self, adapter, dummy_settings, monkeypatch, mocker):
        user_mock = mocker.AsyncMock()

        class MockUserResource:
            async def get(self, *_args, **_kwargs):
                return user_mock

        mock_user_resource = mocker.MagicMock(return_value=MockUserResource())
        monkeypatch.setattr(user_management_bff.adapters.users, "UserResource", mock_user_resource)
        await adapter.configure(dummy_settings)
        result = await adapter.delete_user("test_user1")
        await user_mock.delete.called_once()
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, adapter, dummy_settings, monkeypatch, mocker):
        class MockUserResource:
            async def get(self, *_args, **_kwargs):
                raise NoObject()

        mock_user_resource = mocker.MagicMock(return_value=MockUserResource())
        monkeypatch.setattr(user_management_bff.adapters.users, "UserResource", mock_user_resource)
        await adapter.configure(dummy_settings)
        with pytest.raises(ObjectNotFoundError, match="Object not found: test_user1") as exc_info:
            await adapter.delete_user("test_user1")
        assert exc_info.value.identifier == "test_user1"


@pytest.mark.e2e
class TestKelvinUsersPersistenceAdapterIntegration:
    @pytest.fixture
    def adapter(self):
        return KelvinUsersPersistenceAdapter()

    @pytest.fixture
    def settings(self):
        username = os.environ.get("KELVIN_PERSISTENCE_ADAPTER__USERNAME")
        if not username:
            with open(os.environ["KELVIN_PERSISTENCE_ADAPTER__USERNAME_FILE"]) as fd:
                username = fd.read().strip()
        password = os.environ.get("KELVIN_PERSISTENCE_ADAPTER__PASSWORD")
        if not password:
            with open(os.environ["KELVIN_PERSISTENCE_ADAPTER__PASSWORD_FILE"]) as fd:
                password = fd.read().strip()
        return KelvinPersistenceAdapterSettings(
            url=os.environ["KELVIN_PERSISTENCE_ADAPTER__URL"],
            username=username,
            password=password,
        )

    @pytest.mark.asyncio
    async def test_create_user(self, adapter, settings, delete_user_kelvin):
        await adapter.configure(settings)
        result = await adapter.create_user(
            UserAttributes(
                first_name="firstname",
                last_name="lastname",
                username="test_user1",
                disabled=False,
                schools=["school1"],
                school_classes={},
                roles=["teacher"],
                password="univention1234567890",
            )
        )
        assert result
        assert result == User(
            id="test_user1",
            attributes=UserAttributes(
                last_name="lastname",
                first_name="firstname",
                username="test_user1",
                disabled=False,
                schools=["school1"],
                school_classes={},
                roles=["teacher"],
            ),
        )
        await delete_user_kelvin("test_user1", adapter.kelvin_session)


class TestFileUsersPersistenceAdapter:
    @pytest.fixture
    def adapter(self):
        return FileUsersPersistenceAdapter()

    @pytest.fixture
    def users_json(self, tmpdir):
        mock_users_json_path = tmpdir / "users.json"
        disk_users_json_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../../../dev/data/users.json",
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
        "school,expected_users",
        [
            ("NON_EXISTENT", []),
            (
                "test_school1",
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
                        },
                        "id": "test_user1",
                    }
                ],
            ),
            (
                "test_school2",
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
                        },
                        "id": "test_user3",
                    },
                ],
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_get_users(self, adapter, school, expected_users, users_json):
        await adapter.configure(FileUsersPersistenceAdapterSettings(source=users_json))
        result = await adapter.get_users(school)
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
                roles=["teacher:school:school1"],
            ),
        )

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, adapter, users_json):
        await adapter.configure(FileUsersPersistenceAdapterSettings(source=users_json))
        with pytest.raises(ObjectNotFoundError, match="Object not found: NON_EXISTENT") as exc_info:
            await adapter.get_user("NON_EXISTENT")
        assert exc_info.value.identifier == "NON_EXISTENT"

    @pytest.mark.asyncio
    async def test_delete_user(self, adapter, users_json):
        await adapter.configure(FileUsersPersistenceAdapterSettings(source=users_json))
        # TODO should we check here first that the user exists?
        # It works out now since delete_user raises ObjectNotFoundError
        await adapter.delete_user("user1")
        with pytest.raises(ObjectNotFoundError, match="Object not found: user1") as exc_info:
            await adapter.delete_user("user1")
        assert exc_info.value.identifier == "user1"
