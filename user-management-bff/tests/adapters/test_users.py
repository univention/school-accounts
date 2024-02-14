# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import json
import os

import pytest

import user_management_bff.adapters.users
from user_management_bff.adapters.base import KelvinPersistenceAdapterSettings
from user_management_bff.adapters.users import (
    FileUsersPersistenceAdapter,
    FileUsersPersistenceAdapterSettings,
    KelvinUsersPersistenceAdapter,
)
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
        print(user_management_bff.adapters.users.UserResource)
        result = await adapter.get_users("school1")
        assert result == [
            User(id=user_data["id"], attributes=UserAttributes(**user_data["attributes"]))
            for user_data in input_data
        ]


class TestFileUsersPersistenceAdapter:
    @pytest.fixture
    def adapter(self):
        return FileUsersPersistenceAdapter()

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
    async def test_get_users(self, adapter, school, expected_users):
        await adapter.configure(
            FileUsersPersistenceAdapterSettings(
                source=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "../../../dev/data/users.json",
                )
            )
        )
        result = await adapter.get_users(school)
        assert result == [
            User(id=user["id"], attributes=UserAttributes(**user["attributes"]))
            for user in expected_users
        ]
