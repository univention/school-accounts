# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Any, cast

from httpx import AsyncClient, RequestError
from loguru import logger


async def get_oauth2_settings(well_known_url: str, timeout: int) -> dict[str, Any]:
    async with AsyncClient() as client:
        try:
            response = await client.get(well_known_url, timeout=timeout)
        except RequestError as exc:
            error_msg = f"Could not load oauth2 settings from {well_known_url}: '{exc}'"
            logger.critical(
                "Cannot reach the OAuth2 provider, so no user can log in.",
                well_known_url=well_known_url,
                error=str(exc),
            )
            raise RuntimeError(error_msg)
        if response.status_code != 200:
            error_msg = f"Could not load oauth2 settings from {well_known_url}:" f" '{response.json()}'"
            logger.critical(
                "The OAuth2 provider refused its discovery document, so no user can log in.",
                well_known_url=well_known_url,
                status_code=response.status_code,
                response=response.json(),
            )
            raise RuntimeError(error_msg)
        oauth2_settings = cast("dict[str, object]", response.json())
        logger.trace(
            "Loaded the OAuth2 provider metadata.",
            well_known_url=well_known_url,
            issuer=oauth2_settings.get("issuer"),
            advertised=sorted(key for key in oauth2_settings if key.endswith("_endpoint")),
        )
        return oauth2_settings
