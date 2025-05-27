# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
from collections import defaultdict

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
    ListUserPermissions,
    ListUsersResponse,
    SchoolContextPermission,
)
from user_management_bff.models import Permission, School, SchoolClass, User, UserAttributes, WorkGroup


class TestFastAPIUsersRepresentationAdapter:
    @pytest.fixture()
    def adapter(self):
        return FastAPIUsersRepresentationAdapter()

    @pytest.mark.parametrize(
        "attribute_name,permissions,expected",
        [
            ("first_name", {Permission.read_first_name}, {"value": 1, "access": AttributeAccess.READ}),
            ("first_name", {Permission.write_first_name}, {"value": 1, "access": AttributeAccess.WRITE}),
            (
                "first_name",
                {Permission.read_first_name, Permission.write_first_name},
                {"value": 1, "access": AttributeAccess.WRITE},
            ),
            ("unknown", {}, {"value": None, "access": AttributeAccess.NONE}),
        ],
    )
    def test__get_attribute_dict(self, adapter, attribute_name, permissions, expected):
        assert adapter._get_attribute_dict(attribute_name, 1, permissions) == expected

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
                        "work_groups": {"school1": ["w1a"]},
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
                        "work_groups": {"school1": ["w1a"]},
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
                        "work_groups": {"school2": ["w2b"]},
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
                    allowed_actions=[ListUserPermissions.DELETE],
                    attributes=ListUserFixedAttributes(
                        **{
                            name: {"value": value, "access": AttributeAccess.WRITE}
                            for name, value in transform_user_dict_to_api_users_dict(user_values)[
                                "attributes"
                            ].items()
                        }
                    ),
                )
                for user_values in values
            ]
        )
        schools = [
            School(id=school, display_name=f"{school[0:6].capitalize()} {school[-1]}")
            for user in users
            for school in user.attributes.schools
        ]
        school_classes = defaultdict(list)
        for user in users:
            for school, classes in user.attributes.school_classes.items():
                school_classes[school].extend(
                    SchoolClass(id=sc, display_name=sc, school=school) for sc in classes
                )

        work_groups = defaultdict(list)
        for user in users:
            for school, wgroups in user.attributes.work_groups.items():
                work_groups[school].extend(
                    WorkGroup(id=wg, display_name=wg, school=school) for wg in wgroups
                )

        result = adapter.create_users_representation(
            users=users,
            permissions={
                user_values["id"]: [Permission(permission) for permission in Permission]
                for user_values in values
            },
            school_classes=school_classes,
            work_groups=work_groups,
            schools=schools,
            lang=None,
        )
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
