# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import pytest

from user_management_bff.adapters.api import FastAPIUsersRepresentationAdapter
from user_management_bff.api_models import (
    ListUser,
    ListUserFixedAttributes,
    ListUsersResponse,
)
from user_management_bff.models import User, UserAttributes


class TestFastAPIUsersRepresentationAdapter:
    @pytest.fixture()
    def adapter(self):
        return FastAPIUsersRepresentationAdapter()

    @pytest.mark.parametrize(
        "values",
        [
            [],
            [
                {
                    "id": "user1",
                    "attributes": {
                        "disabled": False,
                        "first_name": "Kim",
                        "last_name": "Klein",
                        "roles": ["teacher:school:school1", "student:school:school2"],
                        "schools": ["school2", "school1"],
                        "username": "kim.klein",
                    },
                }
            ],
            [
                {
                    "id": "user1",
                    "attributes": {
                        "disabled": False,
                        "first_name": "Kim",
                        "last_name": "Klein",
                        "roles": ["teacher:school:school1", "student:school:school2"],
                        "schools": ["school2", "school1"],
                        "username": "kim.klein",
                    },
                },
                {
                    "id": "user2",
                    "attributes": {
                        "disabled": False,
                        "first_name": "Jon",
                        "last_name": "Doe",
                        "roles": ["staff:school:school3"],
                        "schools": ["school3"],
                        "username": "jon.doe",
                    },
                },
            ],
        ],
    )
    def test_create_users_representation(self, values: list[dict], adapter):
        users = [
            User(
                id=user_values["id"],
                attributes=UserAttributes(**user_values["attributes"]),
            )
            for user_values in values
        ]
        expected = ListUsersResponse(
            users=[
                ListUser(
                    id=user_values["id"],
                    attributes=ListUserFixedAttributes(
                        **{
                            name: {"value": value, "visible": True}
                            for name, value in user_values["attributes"].items()
                        }
                    ),
                )
                for user_values in values
            ]
        )
        result = adapter.create_users_representation(users)
        assert result == expected
