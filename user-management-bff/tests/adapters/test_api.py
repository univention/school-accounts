# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import pytest

from user_management_bff.adapters.api import (
    FastAPISchoolsRepresentationAdapter,
    FastAPIUsersRepresentationAdapter,
)
from user_management_bff.api_models import (
    AttributeAccess,
    ListSchool,
    ListSchoolsResponse,
    ListUser,
    ListUserFixedAttributes,
    ListUsersResponse,
    SchoolContextPermission,
)
from user_management_bff.models import Permission, School, User, UserAttributes


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
                        "school_classes": {"school1": ["1a", "2b"], "school2": ["3c"]},
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
                        "school_classes": {"school1": ["1a", "2b"]},
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
                        "school_classes": {"school2": ["1a", "2b"]},
                        "username": "jon.doe",
                    },
                },
            ],
        ],
    )
    def test_create_users_representation(
        self, values: list[dict], adapter, transform_user_dict_to_api_users_dict
    ):
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
                            name: {"value": value, "access": AttributeAccess.READ}
                            for name, value in transform_user_dict_to_api_users_dict(user_values)[
                                "attributes"
                            ].items()
                        }
                    ),
                )
                for user_values in values
            ]
        )
        result = adapter.create_users_representation(users)
        assert result == expected


class TestFastAPISchoolsRepresentationAdapter:
    @pytest.fixture()
    def adapter(self):
        return FastAPISchoolsRepresentationAdapter()

    @pytest.mark.parametrize(
        "values",
        [
            [],
            [
                {"id": "school1", "display_name": "School 1"},
                {"id": "school2", "display_name": "School 2"},
            ],
        ],
    )
    def test_create_schools_representation(self, values: list[dict], adapter):
        schools = [
            School(id=school_values["id"], display_name=school_values["display_name"])
            for school_values in values
        ]
        permissions = {school_values["id"]: [Permission.create_user] for school_values in values}
        expected = ListSchoolsResponse(
            schools=[
                ListSchool(
                    value=school_values["id"],
                    label=school_values["display_name"],
                    permissions=[SchoolContextPermission.ADD],
                )
                for school_values in values
            ]
        )
        result = adapter.create_schools_representation(schools, permissions)
        assert result == expected
