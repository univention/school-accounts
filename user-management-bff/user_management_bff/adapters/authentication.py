# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Authentication adapters.

The interactive UI authenticates the browser with an OAuth2 Authorization Code
flow (with PKCE) against Keycloak and keeps a server-side session, identified by
an opaque, signed cookie. The session stores only what the UI needs - the actor
identifier for permission checks plus the data required for logout and silent
token refresh. Downstream calls (Kelvin/Guardian) use the service account and
never the user's access token, so the access token is not retained.
"""

import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Coroutine, cast
from urllib.parse import urlencode

import httpx
from authlib.integrations.starlette_client import OAuth, OAuthError, StarletteOAuth2App
from itsdangerous import BadSignature, URLSafeSerializer
from loguru import logger
from port_loader import AsyncConfiguredAdapterMixin
from port_loader.models import SETTINGS_NAME_METADATA
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

if sys.version_info >= (3, 12):
    from typing import override  # pyright: ignore[reportUnreachable]
else:
    from typing_extensions import override

from user_management_bff.adapter_registry import ADAPTER_REGISTRY
from user_management_bff.constants import FRONTEND_PREFIX
from user_management_bff.errors import NotAuthenticatedError
from user_management_bff.lang import _
from user_management_bff.models import SessionRecord
from user_management_bff.ports import FastAPIAuthenticationPort, SessionStorePort

_OIDC_CLIENT_NAME = "keycloak"
_COOKIE_SIGNER_SALT = "user-management-session"
_NEXT_SESSION_KEY = "post_login_next"


@dataclass
class CookieSessionAuthenticationAdapterSettings:
    well_known_url: str = field(
        metadata={SETTINGS_NAME_METADATA: "cookie_session_authentication_adapter.well_known_url"}
    )
    client_id: str = field(
        metadata={SETTINGS_NAME_METADATA: "cookie_session_authentication_adapter.client_id"}
    )
    redirect_url: str = field(
        metadata={SETTINGS_NAME_METADATA: "cookie_session_authentication_adapter.redirect_url"}
    )
    cookie_secret: str = field(
        metadata={SETTINGS_NAME_METADATA: "cookie_session_authentication_adapter.cookie_secret"}
    )
    post_logout_redirect_url: str = field(
        default="",
        metadata={
            SETTINGS_NAME_METADATA: "cookie_session_authentication_adapter.post_logout_redirect_url"
        },
    )
    identifier_claim: str = field(
        default="preferred_username",
        metadata={SETTINGS_NAME_METADATA: "cookie_session_authentication_adapter.identifier_claim"},
    )
    scope: str = field(
        default="openid profile email",
        metadata={SETTINGS_NAME_METADATA: "cookie_session_authentication_adapter.scope"},
    )
    cookie_name: str = field(
        default="user_management_session",
        metadata={SETTINGS_NAME_METADATA: "cookie_session_authentication_adapter.cookie_name"},
    )
    cookie_max_age: int = field(
        default=28800,
        metadata={SETTINGS_NAME_METADATA: "cookie_session_authentication_adapter.cookie_max_age"},
    )
    cookie_secure: bool = field(
        default=True,
        metadata={SETTINGS_NAME_METADATA: "cookie_session_authentication_adapter.cookie_secure"},
    )
    request_timeout: int = field(
        default=10,
        metadata={SETTINGS_NAME_METADATA: "cookie_session_authentication_adapter.request_timeout"},
    )


class CookieSessionAuthenticationAdapter(
    FastAPIAuthenticationPort, AsyncConfiguredAdapterMixin[CookieSessionAuthenticationAdapterSettings]
):
    class Config:
        alias: str = "cookie_session"
        cached: bool = True

    def __init__(self) -> None:
        super().__init__()
        self._settings: CookieSessionAuthenticationAdapterSettings | None = None
        self._oauth: OAuth | None = None

    @classmethod
    def get_settings_cls(cls) -> type[CookieSessionAuthenticationAdapterSettings]:
        return CookieSessionAuthenticationAdapterSettings

    @property
    def settings(self) -> CookieSessionAuthenticationAdapterSettings:
        if self._settings is None:
            error_msg = "The settings should never be accessed before the adapter was configured!"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        return self._settings

    async def configure(self, settings: CookieSessionAuthenticationAdapterSettings):
        self._settings = settings
        oauth = OAuth()
        oauth.register(
            name=_OIDC_CLIENT_NAME,
            client_id=settings.client_id,
            server_metadata_url=settings.well_known_url,
            client_kwargs={"scope": settings.scope, "code_challenge_method": "S256"},
        )
        self._oauth = oauth

    def _get_client(self) -> StarletteOAuth2App:
        if self._oauth is None:
            error_msg = "The OAuth client should never be accessed before the adapter was configured!"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        # authlib ships no types for create_client(); safe because configure() always
        # registers _OIDC_CLIENT_NAME as an OAuth2 client before this is ever called.
        return cast(StarletteOAuth2App, self._oauth.create_client(_OIDC_CLIENT_NAME))

    async def _session_store(self) -> SessionStorePort:
        return await ADAPTER_REGISTRY(SessionStorePort)

    @property
    def _serializer(self) -> URLSafeSerializer:
        return URLSafeSerializer(self.settings.cookie_secret, salt=_COOKIE_SIGNER_SALT)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _token_expiry(self, token: dict[str, Any]) -> datetime:
        expires_at = token.get("expires_at")
        if expires_at is not None:
            return datetime.fromtimestamp(expires_at, tz=timezone.utc)
        expires_in = token.get("expires_in", self.settings.cookie_max_age)
        return self._now() + timedelta(seconds=expires_in)

    def _safe_next(self, next_url: str) -> str:
        """Only allow local UI paths as a post-login target (open-redirect guard)."""
        if next_url and next_url.startswith("/") and not next_url.startswith("//"):
            return next_url
        return FRONTEND_PREFIX

    def _set_cookie(self, response: Response, session_id: str) -> None:
        response.set_cookie(
            key=self.settings.cookie_name,
            value=self._serializer.dumps(session_id),
            max_age=self.settings.cookie_max_age,
            httponly=True,
            samesite="lax",
            secure=self.settings.cookie_secure,
            path="/",
        )

    def _read_cookie(self, request: Request) -> str | None:
        raw = request.cookies.get(self.settings.cookie_name)
        if not raw:
            return None
        try:
            return self._serializer.loads(raw)
        except BadSignature:
            logger.warning("Rejected a session cookie with an invalid signature.")
            return None

    @override
    async def login_redirect(self, request: Request, next_url: str = "") -> Response:
        request.session[_NEXT_SESSION_KEY] = self._safe_next(next_url)
        # authlib ships no types for authorize_redirect(); it returns a RedirectResponse.
        return cast(
            Response, await self._get_client().authorize_redirect(request, self.settings.redirect_url)
        )

    @override
    async def complete_login(self, request: Request) -> Response:
        try:
            # authlib ships no types for authorize_access_token(); it returns an
            # OAuth2Token, which is a plain dict subclass.
            token = cast(dict[str, Any], await self._get_client().authorize_access_token(request))
        except OAuthError as exc:
            logger.error("OIDC callback failed: {}", str(exc))
            raise NotAuthenticatedError(_("Not authenticated"))
        claims: dict[str, Any] = token.get("userinfo") or {}
        actor_id = claims.get(self.settings.identifier_claim)
        if not actor_id:
            error_msg = (
                f"The ID token does not contain the identifier claim "
                f"{self.settings.identifier_claim}. Please check the settings of the oauth provider."
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        record = SessionRecord(
            actor_id=actor_id,
            sub=claims.get("sub", ""),
            kc_sid=claims.get("sid"),
            expires_at=self._token_expiry(token),
            refresh_token=token.get("refresh_token"),
            id_token=token.get("id_token"),
        )
        store = await self._session_store()
        session_id = await store.create(record)
        logger.info("Established a session for actor.", actor_id=actor_id)
        next_url = self._safe_next(request.session.pop(_NEXT_SESSION_KEY, ""))
        response = RedirectResponse(next_url, status_code=303)
        self._set_cookie(response, session_id)
        return response

    @override
    async def logout(self, request: Request) -> Response:
        id_token = None
        session_id = self._read_cookie(request)
        if session_id is not None:
            store = await self._session_store()
            record = await store.get(session_id)
            if record is not None:
                id_token = record.id_token
            await store.delete(session_id)
        target = await self._end_session_url(id_token)
        response = RedirectResponse(target, status_code=303)
        response.delete_cookie(self.settings.cookie_name, path="/")
        return response

    async def _end_session_url(self, id_token: str | None) -> str:
        metadata = await self._get_client().load_server_metadata()
        end_session_endpoint = metadata.get("end_session_endpoint")
        logout_redirect = self.settings.post_logout_redirect_url or FRONTEND_PREFIX
        if not end_session_endpoint:
            return logout_redirect
        params = {"post_logout_redirect_uri": logout_redirect}
        if id_token:
            params["id_token_hint"] = id_token
        return f"{end_session_endpoint}?{urlencode(params)}"

    async def _refresh(
        self, session_id: str, record: SessionRecord, store: SessionStorePort
    ) -> SessionRecord:
        if not record.refresh_token:
            await store.delete(session_id)
            raise NotAuthenticatedError(_("Not authenticated"))
        metadata = await self._get_client().load_server_metadata()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                metadata["token_endpoint"],
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": record.refresh_token,
                    "client_id": self.settings.client_id,
                },
                timeout=self.settings.request_timeout,
            )
        if response.status_code != 200:
            logger.info("Session token refresh failed; requiring re-login.", actor_id=record.actor_id)
            await store.delete(session_id)
            raise NotAuthenticatedError(_("Not authenticated"))
        token = response.json()
        updated = record.model_copy(
            update={
                "expires_at": self._token_expiry(token),
                "refresh_token": token.get("refresh_token") or record.refresh_token,
                "id_token": token.get("id_token") or record.id_token,
            }
        )
        await store.update(session_id, updated)
        return updated

    async def _authenticate(self, request: Request, store: SessionStorePort) -> str:
        session_id = self._read_cookie(request)
        if session_id is None:
            raise NotAuthenticatedError(_("Not authenticated"))
        record = await store.get(session_id)
        if record is None:
            raise NotAuthenticatedError(_("Not authenticated"))
        if record.expires_at <= self._now():
            record = await self._refresh(session_id, record, store)
        return record.actor_id

    async def get_authentication_dependency(self) -> Callable[..., Coroutine[Any, Any, str]]:
        async def _dep(request: Request) -> str:
            return await self.get_authenticated_id(request)

        return _dep

    async def get_authenticated_id(self, request: Request) -> str:
        store = await self._session_store()
        return await self._authenticate(request, store)


class AlwaysAuthenticatedAdapter(FastAPIAuthenticationPort):
    class Config:
        alias = "always_authenticated"
        cached = True

    async def get_authentication_dependency(self) -> Callable[..., Coroutine[Any, Any, str]]:
        async def _dep():
            return "dev"

        return _dep

    async def get_authenticated_id(self, request: Request) -> str:
        return "dev"


class NeverAuthenticatedAdapter(FastAPIAuthenticationPort):
    class Config:
        alias: str = "never_authenticated"
        cached: bool = True

    async def get_authentication_dependency(self) -> Callable:
        def _dep():
            raise NotAuthenticatedError(_("Never authenticated."))

        return _dep

    async def get_authenticated_id(self, request: Request) -> str:
        raise NotAuthenticatedError(_("Never authenticated."))
