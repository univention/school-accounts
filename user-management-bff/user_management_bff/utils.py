# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Any

from httpx import AsyncClient, RequestError


async def get_oauth2_settings(well_known_url: str, timeout: int) -> dict[str, Any]:
    async with AsyncClient() as client:
        try:
            response = await client.get(well_known_url, timeout=timeout)
        except RequestError as exc:
            raise RuntimeError(f"Could not load oauth2 settings from {well_known_url}: '{exc}'")
        if response.status_code != 200:
            raise RuntimeError(
                f"Could not load oauth2 settings from {well_known_url}:" f" '{response.json()}'"
            )
        return response.json()
