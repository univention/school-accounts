# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Any

from httpx import AsyncClient, RequestError
from loguru import logger


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
