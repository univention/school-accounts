# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Type

import jwt
from fastapi import Depends
from fastapi.security import OAuth2AuthorizationCodeBearer
from jwt import PyJWKClient
from loguru import logger
from port_loader import AsyncConfiguredAdapterMixin
from port_loader.models import SETTINGS_NAME_METADATA
from starlette.requests import Request

from user_management_bff.errors import NotAuthenticatedError
from user_management_bff.lang import _
from user_management_bff.ports import FastAPIAuthenticationPort
from user_management_bff.utils import get_oauth2_settings


@dataclass
class Oauth2FastAPIAuthenticationAdapterSettings:
    well_known_url: str = field(
        metadata={SETTINGS_NAME_METADATA: "oauth2_fastapi_authentication_adapter.well_known_url"}
    )
    audience: str = field(
        metadata={SETTINGS_NAME_METADATA: "oauth2_fastapi_authentication_adapter.audience"}
    )
    request_timeout: int = field(
        default=10,
        metadata={SETTINGS_NAME_METADATA: "oauth2_fastapi_authentication_adapter.request_timeout"},
    )
    identifier_claim: str = field(
        default="sub",
        metadata={SETTINGS_NAME_METADATA: "oauth2_fastapi_authentication_adapter.identifier_claim"},
    )


class Oauth2FastAPIAuthenticationAdapter(FastAPIAuthenticationPort, AsyncConfiguredAdapterMixin):

    class Config:
        alias = "oauth2"
        cached = True

    def __init__(self):
        super().__init__()
        self._settings = None
        self._oauth2_settings = None

    @classmethod
    def get_settings_cls(cls) -> Type[Oauth2FastAPIAuthenticationAdapterSettings]:
        return Oauth2FastAPIAuthenticationAdapterSettings

    @property
    def settings(self) -> Oauth2FastAPIAuthenticationAdapterSettings:
        if self._settings is None:
            error_msg = "The settings should never be accessed before the adapter was configured!"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        return self._settings

    async def _get_oauth2_settings(self) -> dict[str, Any]:
        return await get_oauth2_settings(self.settings.well_known_url, self.settings.request_timeout)

    def _get_oauth2_scheme(
        self, authorization_endpoint: str, token_endpoint: str
    ) -> OAuth2AuthorizationCodeBearer:
        return OAuth2AuthorizationCodeBearer(
            authorizationUrl=authorization_endpoint,
            tokenUrl=token_endpoint,
            scopes={"openid": "scope for openid"},
        )

    async def configure(self, settings: Oauth2FastAPIAuthenticationAdapterSettings):
        self._settings = settings

    async def get_authentication_dependency(self) -> Callable[[], Coroutine[Any, Any, str]]:
        oauth2_settings = await self._get_oauth2_settings()
        oauth2_scheme = self._get_oauth2_scheme(
            oauth2_settings["authorization_endpoint"], oauth2_settings["token_endpoint"]
        )
        jwks_client = PyJWKClient(oauth2_settings["jwks_uri"], timeout=self.settings.request_timeout)

        async def _oauth2_authentication(token: str = Depends(oauth2_scheme)) -> str:
            try:
                decoded_token = jwt.decode(
                    token,
                    jwks_client.get_signing_key_from_jwt(token).key,
                    algorithms=["RS256"],
                    audience=self.settings.audience,
                    issuer=oauth2_settings["issuer"],
                    leeway=1,
                    options={"require": ["exp", "iss", "aud", "sub", "iat", "jti"]},
                )
            except jwt.exceptions.InvalidTokenError as exc:
                logger.error("Error while decoding JWT token: Invalid Token.")
                raise NotAuthenticatedError(_("Not authenticated")) from exc
            if self.settings.identifier_claim not in decoded_token:
                error_msg = (
                    f"The token does not contain the identifier claim {self.settings.identifier_claim}. "
                    f"Please check the settings of the oauth provider."
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            return decoded_token[self.settings.identifier_claim]

        return _oauth2_authentication

    async def get_authenticated_id(self, request: Request) -> str:
        oauth2_settings = await self._get_oauth2_settings()
        oauth2_scheme = self._get_oauth2_scheme(
            oauth2_settings["authorization_endpoint"], oauth2_settings["token_endpoint"]
        )
        dep = await self.get_authentication_dependency()
        return await dep(token=await oauth2_scheme(request))  # type: ignore[call-arg]


class AlwaysAuthenticatedAdapter(FastAPIAuthenticationPort):

    class Config:
        alias = "always_authenticated"
        cached = True

    async def get_authentication_dependency(self) -> Callable[[], Coroutine[Any, Any, str]]:
        async def _dep():
            return "dev"

        return _dep

    async def get_authenticated_id(self, request: Request) -> str:
        return "dev"


class NeverAuthenticatedAdapter(FastAPIAuthenticationPort):

    class Config:
        alias = "never_authenticated"
        cached = True

    async def get_authentication_dependency(self) -> Callable:
        def _dep():
            raise NotAuthenticatedError(_("Never authenticated."))

        return _dep

    async def get_authenticated_id(self, request: Request) -> str:
        raise NotAuthenticatedError(_("Never authenticated."))
