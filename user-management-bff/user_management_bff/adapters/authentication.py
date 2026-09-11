# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Authentication adapters.

The interactive UI authenticates the browser with an OAuth2 Authorization Code
flow (with PKCE) against Keycloak and keeps the resulting session entirely in an
encrypted cookie - no server-side storage, and therefore no way to revoke a
session before it expires.

The OIDC client is confidential: the token and refresh calls leave the browser
out of it entirely, so the client secret never reaches a user agent.
"""

from __future__ import annotations

import secrets
import sys
from collections.abc import Coroutine
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, cast
from urllib.parse import urlencode

import httpx
from authlib.integrations.starlette_client import OAuth, OAuthError, StarletteOAuth2App
from loguru import logger
from port_loader import AsyncConfiguredAdapterMixin
from port_loader.models import SETTINGS_NAME_METADATA
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

if sys.version_info >= (3, 12):  # pragma: no cover
    from typing import override  # pyright: ignore[reportUnreachable]
else:
    from typing_extensions import override

from user_management_bff.constants import FRONTEND_PREFIX, SESSION_COOKIE_PATH
from user_management_bff.errors import NotAuthenticatedError
from user_management_bff.lang import _
from user_management_bff.models import SessionRecord
from user_management_bff.ports import FastAPIAuthenticationPort
from user_management_bff.session_cookie import SessionCookieCodec

_OIDC_CLIENT_NAME = "keycloak"
_NEXT_SESSION_KEY = "post_login_next"

# A SessionRecord means "write this cookie", None means "delete it", and an
# absent attribute means the request did not touch the session.
_PENDING_SESSION_ATTR = "pending_session"
_NO_PENDING_SESSION = object()


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
    client_secret: str = field(
        default="",
        metadata={SETTINGS_NAME_METADATA: "cookie_session_authentication_adapter.client_secret"},
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
    display_name_claim: str = field(
        default="name",
        metadata={SETTINGS_NAME_METADATA: "cookie_session_authentication_adapter.display_name_claim"},
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
        self._codec: SessionCookieCodec | None = None

    @classmethod
    @override
    def get_settings_cls(cls) -> type[CookieSessionAuthenticationAdapterSettings]:
        return CookieSessionAuthenticationAdapterSettings

    @property
    def settings(self) -> CookieSessionAuthenticationAdapterSettings:
        if self._settings is None:
            error_msg = "The settings should never be accessed before the adapter was configured!"
            logger.critical("The authentication backend is not configured, so nobody can log in.")
            raise RuntimeError(error_msg)
        return self._settings

    @override
    async def configure(self, settings: CookieSessionAuthenticationAdapterSettings):
        self._settings = settings
        self._codec = None
        oauth = OAuth()
        oauth.register(
            name=_OIDC_CLIENT_NAME,
            client_id=settings.client_id,
            client_secret=settings.client_secret,
            server_metadata_url=settings.well_known_url,
            client_kwargs={
                "scope": settings.scope,
                "code_challenge_method": "S256",
                "timeout": settings.request_timeout,
            },
        )
        self._oauth = oauth

    def _get_client(self) -> StarletteOAuth2App:
        if self._oauth is None:
            error_msg = "The OAuth client should never be accessed before the adapter was configured!"
            logger.critical("The OAuth client is not configured, so nobody can log in.")
            raise RuntimeError(error_msg)
        # authlib ships no types for create_client(); safe because configure() always
        # registers _OIDC_CLIENT_NAME as an OAuth2 client before this is ever called.
        return cast(StarletteOAuth2App, self._oauth.create_client(_OIDC_CLIENT_NAME))

    @property
    def _cookie_codec(self) -> SessionCookieCodec:
        if self._codec is None:
            self._codec = SessionCookieCodec(self.settings.cookie_secret)
        return self._codec

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

    def _absolute_deadline(self, record: SessionRecord) -> datetime:
        return record.created_at + timedelta(seconds=self.settings.cookie_max_age)

    def _set_pending_session(self, request: Request, record: SessionRecord | None) -> None:
        setattr(request.state, _PENDING_SESSION_ATTR, record)

    def _write_session(self, response: Response, record: SessionRecord) -> None:
        remaining = int((self._absolute_deadline(record) - self._now()).total_seconds())
        response.set_cookie(
            key=self.settings.cookie_name,
            value=self._cookie_codec.encode(record),
            max_age=max(remaining, 0),
            httponly=True,
            samesite="lax",
            secure=self.settings.cookie_secure,
            path=SESSION_COOKIE_PATH,
        )

    def _delete_session(self, response: Response) -> None:
        response.delete_cookie(self.settings.cookie_name, path=SESSION_COOKIE_PATH)
        if SESSION_COOKIE_PATH != "/":
            # A browser can still hold a copy at "/", which shadows the narrower one because
            # same-name cookies parse last-wins; clearing only one path locks that browser out.
            response.delete_cookie(self.settings.cookie_name, path="/")

    def _read_session(self, request: Request) -> SessionRecord | None:
        raw = request.cookies.get(self.settings.cookie_name)
        if not raw:
            return None
        record = self._cookie_codec.decode(raw)
        if record is None:
            self._set_pending_session(request, None)
            return None
        if self._now() >= self._absolute_deadline(record):
            logger.info(
                "Session reached its maximum lifetime; requiring re-login.", actor_id=record.actor_id
            )
            self._set_pending_session(request, None)
            return None
        return record

    @override
    async def login_redirect(self, request: Request, next_url: str = "") -> Response:
        safe_next = self._safe_next(next_url)
        if next_url and safe_next != next_url:
            logger.info(
                "Rejected a non-local post-login target and sent the user to the start page.",
                requested=next_url,
            )
        logger.debug("Starting the OIDC login.", post_login_target=safe_next)
        request.session[_NEXT_SESSION_KEY] = safe_next
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
            logger.warning(
                "The OIDC callback failed, so the login did not complete. Usually a login "
                "left open too long - starting it again resolves it.",
                error=exc.error,
                description=exc.description,
            )
            raise NotAuthenticatedError(_("Not authenticated"))
        claims: dict[str, Any] = token.get("userinfo") or {}
        actor_id = claims.get(self.settings.identifier_claim)
        if not actor_id:
            error_msg = (
                f"The ID token does not contain the identifier claim "
                f"{self.settings.identifier_claim}. Please check the settings of the oauth provider."
            )
            logger.critical(
                "The ID token lacks the configured identifier claim, so every login fails. "
                "Map this claim into the ID token of the app's Keycloak client.",
                identifier_claim=self.settings.identifier_claim,
                available_claims=sorted(claims),
            )
            raise RuntimeError(error_msg)
        record = SessionRecord(
            actor_id=actor_id,
            display_name=cast(str, claims.get(self.settings.display_name_claim) or actor_id),
            sub=claims.get("sub", ""),
            kc_sid=claims.get("sid"),
            created_at=self._now(),
            expires_at=self._token_expiry(token),
            refresh_token=token.get("refresh_token"),
            id_token=token.get("id_token"),
            csrf_token=secrets.token_urlsafe(32),
        )
        logger.info(
            "Established a session for actor.",
            actor_id=actor_id,
            expires_at=record.expires_at,
            has_refresh_token=bool(record.refresh_token),
        )
        next_url = self._safe_next(request.session.pop(_NEXT_SESSION_KEY, ""))
        response = RedirectResponse(next_url, status_code=303)
        self._write_session(response, record)
        return response

    @override
    async def logout(self, request: Request) -> Response:
        record = self._read_session(request)
        if record is not None:
            logger.info("Ended a session for actor.", actor_id=record.actor_id)
        target = await self._end_session_url(record.id_token if record is not None else None)
        response = RedirectResponse(target, status_code=303)
        self._delete_session(response)
        return response

    async def _end_session_url(self, id_token: str | None) -> str:
        metadata = await self._get_client().load_server_metadata()
        end_session_endpoint = metadata.get("end_session_endpoint")
        logout_redirect = self.settings.post_logout_redirect_url or FRONTEND_PREFIX
        if not end_session_endpoint:
            logger.warning(
                "The OAuth2 provider advertises no end-session endpoint, so logging out here "
                "leaves the browser signed in at the provider. Enable it at the provider.",
                well_known_url=self.settings.well_known_url,
            )
            return logout_redirect
        params = {"post_logout_redirect_uri": logout_redirect}
        if id_token:
            params["id_token_hint"] = id_token
        return f"{end_session_endpoint}?{urlencode(params)}"

    async def _refresh(self, record: SessionRecord) -> SessionRecord:
        if not record.refresh_token:
            logger.debug(
                "The expired session has no refresh token; requiring re-login.",
                actor_id=record.actor_id,
            )
            raise NotAuthenticatedError(_("Not authenticated"))
        try:
            token = cast(
                dict[str, object],
                await self._get_client().fetch_access_token(  # pyright: ignore[reportUnknownMemberType]
                    grant_type="refresh_token", refresh_token=record.refresh_token
                ),
            )
        except (OAuthError, httpx.HTTPError, ValueError) as exc:
            logger.info(
                "Session token refresh failed; requiring re-login.",
                actor_id=record.actor_id,
                reason=str(exc),
            )
            raise NotAuthenticatedError(_("Not authenticated"))
        actor_id = record.actor_id
        if token.get("id_token"):
            actor_id = await self._refreshed_actor_id(token, record)
        # created_at stays put: it anchors the absolute lifetime.
        updated = record.model_copy(
            update={
                "actor_id": actor_id,
                "expires_at": self._token_expiry(token),
                "refresh_token": token.get("refresh_token") or record.refresh_token,
                "id_token": token.get("id_token") or record.id_token,
            }
        )
        logger.debug(
            "Refreshed the session token.", actor_id=updated.actor_id, expires_at=updated.expires_at
        )
        return updated

    async def _refreshed_actor_id(self, token: dict[str, object], record: SessionRecord) -> str:
        """Re-derive the actor from a refreshed ID token, rejecting a changed subject.

        The actor is the principal every permission check is made against, so it
        cannot be left at whatever the login established.
        """
        try:
            # The nonce belongs to the login request; a refreshed ID token carries
            # no nonce claim to compare one against.
            claims = cast(
                dict[str, object],
                await self._get_client().parse_id_token(  # pyright: ignore[reportUnknownMemberType]
                    token, nonce=None
                ),
            )
        except Exception as exc:
            # Broad on purpose: the signature and claim errors come from authlib's
            # JOSE backend, which it swaps out between releases.
            logger.warning(
                "The refreshed ID token could not be validated; requiring re-login. If this "
                "repeats for every user, check the provider's signing keys and issuer.",
                actor_id=record.actor_id,
                reason=str(exc),
            )
            raise NotAuthenticatedError(_("Not authenticated"))
        if claims.get("sub") != record.sub:
            logger.warning(
                "The refreshed ID token belongs to a different subject; requiring re-login. "
                "Usually the account was deleted and recreated at the provider.",
                actor_id=record.actor_id,
                previous_sub=record.sub,
                refreshed_sub=claims.get("sub"),
            )
            raise NotAuthenticatedError(_("Not authenticated"))
        actor_id = claims.get(self.settings.identifier_claim)
        if not isinstance(actor_id, str) or not actor_id:
            logger.warning(
                "The refreshed ID token lacks the configured identifier claim; requiring "
                "re-login. Map this claim into the ID token of the app's Keycloak client.",
                actor_id=record.actor_id,
                identifier_claim=self.settings.identifier_claim,
            )
            raise NotAuthenticatedError(_("Not authenticated"))
        return actor_id

    @override
    async def get_authentication_dependency(self) -> Callable[..., Coroutine[Any, Any, str]]:
        async def _dep(request: Request) -> str:
            return await self.get_authenticated_id(request)

        return _dep

    @override
    async def get_authenticated_id(self, request: Request) -> str:
        record = self._read_session(request)
        if record is None:
            logger.debug("The request carries no usable session cookie.")
            raise NotAuthenticatedError(_("Not authenticated"))
        if record.expires_at <= self._now():
            logger.debug(
                "The session's token has expired; refreshing it.",
                actor_id=record.actor_id,
                expires_at=record.expires_at,
            )
            try:
                record = await self._refresh(record)
            except NotAuthenticatedError:
                # Keeping the cookie would retry the dead refresh token on every later request.
                self._set_pending_session(request, None)
                raise
            self._set_pending_session(request, record)
        return record.actor_id

    @override
    async def get_display_name(self, request: Request) -> str:
        record = self._read_session(request)
        return record.display_name if record is not None else ""

    @override
    async def apply_pending_session_cookie(self, request: Request, response: Response) -> None:
        pending = getattr(request.state, _PENDING_SESSION_ATTR, _NO_PENDING_SESSION)
        if isinstance(pending, SessionRecord):
            self._write_session(response, pending)
        elif pending is None:
            self._delete_session(response)

    @staticmethod
    def verify_csrf(submitted: str | None, record: SessionRecord) -> bool:
        if not submitted:
            return False
        return secrets.compare_digest(submitted.encode(), record.csrf_token.encode())

    @override
    async def issue_csrf_token(self, request: Request) -> str:
        record = self._read_session(request)
        return record.csrf_token if record is not None else ""

    @override
    async def check_csrf(self, request: Request, submitted: str | None) -> bool:
        record = self._read_session(request)
        if record is None or not self.verify_csrf(submitted, record):
            logger.warning(
                "Rejected an unsafe request: the CSRF token is missing or does not match. "
                "Usually a page opened before the app restarted - reload it and retry.",
                actor_id=record.actor_id if record else None,
                path=request.url.path,
                token_submitted=bool(submitted),
            )
            return False
        return True


@dataclass
class AlwaysAuthenticatedAdapterSettings:
    actor_id: str = field(
        default="dev",
        metadata={SETTINGS_NAME_METADATA: "always_authenticated_adapter.actor_id"},
    )


class AlwaysAuthenticatedAdapter(
    FastAPIAuthenticationPort, AsyncConfiguredAdapterMixin[AlwaysAuthenticatedAdapterSettings]
):
    class Config:
        alias: str = "always_authenticated"
        cached: bool = True

    def __init__(self) -> None:
        # Usable un-configured (e.g. instantiated directly in a test) - defaults
        # to the same "dev" actor `configure()` would land on with no env override.
        self._settings: AlwaysAuthenticatedAdapterSettings = AlwaysAuthenticatedAdapterSettings()

    @classmethod
    @override
    def get_settings_cls(cls) -> type[AlwaysAuthenticatedAdapterSettings]:
        return AlwaysAuthenticatedAdapterSettings

    @override
    async def configure(self, settings: AlwaysAuthenticatedAdapterSettings) -> None:
        self._settings = settings
        logger.warning(
            "Authentication is disabled: every request acts as one fixed actor. Outside "
            "development, select CookieSessionAuthenticationAdapter instead.",
            actor_id=settings.actor_id,
        )

    @override
    async def get_authentication_dependency(self) -> Callable[..., Coroutine[Any, Any, str]]:
        # Async is required by the authentication port contract
        async def _dep() -> str:  # NOSONAR(S7503)
            return self._settings.actor_id

        return _dep

    @override
    async def get_authenticated_id(self, request: Request) -> str:
        return self._settings.actor_id


class NeverAuthenticatedAdapter(FastAPIAuthenticationPort):
    class Config:
        alias: str = "never_authenticated"
        cached: bool = True

    @override
    async def get_authentication_dependency(self) -> Callable[..., Coroutine[Any, Any, str]]:
        def _dep():
            raise NotAuthenticatedError(_("Never authenticated."))

        return _dep

    @override
    async def get_authenticated_id(self, request: Request) -> str:
        raise NotAuthenticatedError(_("Never authenticated."))
