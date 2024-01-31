# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from .models import UsersGetRequest
from .ports import UsersGetRepresentation, UsersPersistencePort, UsersRepresentationPort


async def get_users(
    users_get_adapter: UsersPersistencePort,
    representation_port: UsersRepresentationPort[UsersGetRepresentation],
    request_data: UsersGetRequest,
) -> UsersGetRepresentation:
    users = await users_get_adapter.get_users(request_data.school)
    return representation_port.create_users_representation(users)
