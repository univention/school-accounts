# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
from typing import Any

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

    @staticmethod
    def _get_attribute_dict(
        attribute_name: str, value: Any, permissions: set[Permission]
    ) -> dict[str, Any]:
        result = {"value": None, "access": AttributeAccess.NONE}
        try:
            if Permission(f"read-{attribute_name}") in permissions:
                result["access"] = AttributeAccess.READ
                result["value"] = value
        except ValueError:
            pass
        try:
            if Permission(f"write-{attribute_name}") in permissions:
                result["access"] = AttributeAccess.WRITE
                result["value"] = value
        except ValueError:
            pass
        return result

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

    def create_user_representation(self, user: User, permissions: set[Permission]) -> CreateUserResponse:
        return CreateUserResponse(
            user=CreateUserResponseUser(
                id=user.id,
                attributes=ListUserFixedAttributes(
                    username=ListUserAttribute[str](
                        **self._get_attribute_dict("username", user.attributes.username, permissions)
                    ),
                    last_name=ListUserAttribute[str](
                        **self._get_attribute_dict("last_name", user.attributes.last_name, permissions)
                    ),
                    first_name=ListUserAttribute[str](
                        **self._get_attribute_dict("first_name", user.attributes.first_name, permissions)
                    ),
                    activated=ListUserAttribute[bool](
                        **self._get_attribute_dict("disabled", not user.attributes.disabled, permissions)
                    ),
                    classes=ListUserAttribute[list[str]](
                        **self._get_attribute_dict(
                            "school_classes",
                            [
                                f"{school}:{school_class}"
                                for school, school_classes in user.attributes.school_classes.items()
                                for school_class in school_classes
                            ],
                            permissions,
                        )
                    ),
                    schools=ListUserAttribute[list[str]](
                        **self._get_attribute_dict(
                            "schools", [school for school in user.attributes.schools], permissions
                        )
                    ),
                    roles=ListUserAttribute[list[str]](
                        **self._get_attribute_dict(
                            "roles", [role for role in user.attributes.roles], permissions
                        )
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
