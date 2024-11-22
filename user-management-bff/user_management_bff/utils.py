# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Any

from httpx import AsyncClient, RequestError
from loguru import logger

from user_management_bff.api_models import UserCreateRequest
from user_management_bff.models import Permission, UserPatchRequest


async def get_oauth2_settings(well_known_url: str, timeout: int) -> dict[str, Any]:
    async with AsyncClient() as client:
        try:
            response = await client.get(well_known_url, timeout=timeout)
        except RequestError as exc:
            error_msg = f"Could not load oauth2 settings from {well_known_url}: '{exc}'"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        if response.status_code != 200:
            error_msg = f"Could not load oauth2 settings from {well_known_url}:" f" '{response.json()}'"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        return response.json()


def get_required_permissions_for_create_request(request_data: UserCreateRequest) -> set[Permission]:
    field_permission_mapping = {"school": "write-schools"}
    required_permissions = {
        Permission(field_permission_mapping.get(field_name, f"write-{field_name}"))
        for field_name in request_data.model_fields_set
    }
    required_permissions.add(Permission.create_user)
    return required_permissions


def get_required_permissions_for_patch_request(request_data: UserPatchRequest) -> set[Permission]:
    return {Permission(f"write-{field_name}") for field_name in request_data.attributes.model_fields_set}
