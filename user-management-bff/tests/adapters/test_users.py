# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import json
import os

import pytest

from user_management_bff.adapters.users import (
    FileUsersPersistenceAdapter,
    FileUsersPersistenceAdapterSettings,
)
from user_management_bff.models import User, UserAttributes


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
                            "username": "firstname2.lastname2",
                        },
                        "id": "test_user2",
                    },
                    {
                        "attributes": {
                            "disabled": False,
                            "first_name": "firstname3",
                            "last_name": "lastname3",
                            "roles": ["teacher:school:test_school2", "student:school:test_school3"],
                            "schools": ["test_school2", "test_school3"],
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
                    os.path.dirname(os.path.abspath(__file__)), "../../../dev/data/users.json"
                )
            )
        )
        result = adapter.get_users(school)
        assert result == [
            User(id=user["id"], attributes=UserAttributes(**user["attributes"]))
            for user in expected_users
        ]
