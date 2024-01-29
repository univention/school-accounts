# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from ..api_models import (
    ListUser,
    ListUserFixedAttributes,
    ListUsersResponse,
)
from ..models import User
from ..ports import UsersRepresentationPort


class FastAPIUsersRepresentationAdapter(UsersRepresentationPort[ListUsersResponse]):
    def create_users_representation(self, users: list[User]) -> ListUsersResponse:
        list_users = [
            ListUser(
                id=user.id,
                attributes=ListUserFixedAttributes(
                    **{
                        name: {"value": value, "visible": True}
                        for name, value in user.attributes.model_dump().items()
                    }
                ),
            )
            for user in users
        ]
        return ListUsersResponse(users=list_users)
