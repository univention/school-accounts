# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from ..api_models import (
    AttributeAccess,
    ListSchool,
    ListSchoolsResponse,
    ListUser,
    ListUserFixedAttributes,
    ListUsersResponse,
    SchoolContextPermission,
)
from ..models import Permission, School, User
from ..ports import SchoolsRepresentationPort, UsersRepresentationPort


class FastAPIUsersRepresentationAdapter(UsersRepresentationPort[ListUsersResponse]):
    def create_users_representation(self, users: list[User]) -> ListUsersResponse:
        list_users = [
            ListUser(
                id=user.id,
                attributes=ListUserFixedAttributes(
                    **{
                        **{
                            name: {"value": value, "access": AttributeAccess.READ}
                            for name, value in user.attributes.model_dump().items()
                        },
                        "activated": {
                            "value": not user.attributes.disabled,
                            "access": AttributeAccess.READ,
                        },
                        "classes": {
                            "value": [
                                f"{school}:{school_class}"
                                for school, school_classes in user.attributes.school_classes.items()
                                for school_class in school_classes
                            ],
                            "access": AttributeAccess.READ,
                        },
                    },
                ),
            )
            for user in users
        ]
        return ListUsersResponse(users=list_users)


class FastAPISchoolsRepresentationAdapter(SchoolsRepresentationPort[ListSchoolsResponse]):
    def create_schools_representation(
        self, schools: list[School], permissions: dict[str, list[Permission]]
    ) -> ListSchoolsResponse:
        list_schools = [
            ListSchool(
                label=school.display_name,
                value=school.id,
                permissions=(
                    [SchoolContextPermission.ADD]
                    if "create-user" in permissions.get(school.id, [])
                    else []
                ),
            )
            for school in schools
        ]
        return ListSchoolsResponse(schools=list_schools)
