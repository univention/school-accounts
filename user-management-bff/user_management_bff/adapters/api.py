# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from ..api_models import (
    AttributeAccess,
    CreateUserResponse,
    CreateUserResponseUser,
    ListSchool,
    ListSchoolsResponse,
    ListUser,
    ListUserAttribute,
    ListUserFixedAttributes,
    ListUserPermissions,
    ListUsersResponse,
    SchoolContextPermission,
)
from ..models import Permission, School, User
from ..ports import SchoolsRepresentationPort, UsersRepresentationPort


class FastAPIUsersRepresentationAdapter(UsersRepresentationPort[ListUsersResponse, CreateUserResponse]):
    def create_users_representation(self, users: list[User]) -> ListUsersResponse:
        list_users = [
            ListUser(
                id=user.id,
                # TODO replace hard coded permission
                allowed_actions=[ListUserPermissions.DELETE],
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

    def create_user_representation(self, user: User) -> CreateUserResponse:
        return CreateUserResponse(
            user=CreateUserResponseUser(
                id=user.id,
                attributes=ListUserFixedAttributes(
                    username=ListUserAttribute[str](
                        value=user.attributes.username, access=AttributeAccess.READ
                    ),
                    last_name=ListUserAttribute[str](
                        value=user.attributes.last_name, access=AttributeAccess.READ
                    ),
                    first_name=ListUserAttribute[str](
                        value=user.attributes.first_name, access=AttributeAccess.READ
                    ),
                    activated=ListUserAttribute[bool](
                        value=not user.attributes.disabled, access=AttributeAccess.READ
                    ),
                    classes=ListUserAttribute[list[str]](
                        value=[
                            f"{school}:{school_class}"
                            for school, school_classes in user.attributes.school_classes.items()
                            for school_class in school_classes
                        ],
                        access=AttributeAccess.READ,
                    ),
                    schools=ListUserAttribute[list[str]](
                        value=[school for school in user.attributes.schools],
                        access=AttributeAccess.READ,
                    ),
                    roles=ListUserAttribute[list[str]](
                        value=[role for role in user.attributes.roles],
                        access=AttributeAccess.READ,
                    ),
                ),
            )
        )


class FastAPISchoolsRepresentationAdapter(SchoolsRepresentationPort[ListSchoolsResponse]):
    def create_schools_representation(
        self, schools: list[School], permissions: dict[str, list[Permission]]
    ) -> ListSchoolsResponse:
        sorted_schools = sorted(schools, key=lambda x: x.display_name)
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
            for school in sorted_schools
        ]
        return ListSchoolsResponse(schools=list_schools)
