# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import os
from abc import ABC
from collections.abc import AsyncGenerator, AsyncIterator, Awaitable, Callable, Generator, Iterator
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import Protocol, Type, TypeVar
from urllib.parse import quote

import httpx
from async_property import async_property
from loguru import logger
from port_loader import AsyncConfiguredAdapterMixin
from port_loader.models import SETTINGS_NAME_METADATA
from typing_extensions import override
from ucsschool.kelvin.client import InvalidRequest, ServerError, Session
from ucsschool.kelvin.client.session import Token

from ..errors import KelvinAPIUnavailableError

# this app supports the Kelvin v2 API only, so the version is pinned here.
# The client library still defaults to v1
KELVIN_API_VERSION = "v2"

# The client defaults to 10s, which a password write outruns: it runs the ucsschool
# import framework, far slower than an attribute change.
KELVIN_TIMEOUT_SECONDS = float(os.environ.get("USER_MANAGEMENT__KELVIN_TIMEOUT_SECONDS", "60"))

# The client keeps its token on the session and a session lives for one request,
# so every page view re-authenticated: a password verification against LDAP for
# a credential Kelvin issues with an hour's life. The token is the service
# account's, not the request's, so it is shared across requests for as long as
# the client considers it valid.
# Process-wide on purpose: what it saves is exactly the per-request login.
_shared_token: Token | None = None


def forget_shared_token() -> None:
    """Drop the shared token, so the next session mints one."""
    global _shared_token
    _shared_token = None


class _KelvinSession(Session):
    @override
    async def request(
        self,
        async_request_method: Callable[..., Awaitable[httpx.Response]],
        url: str,
        return_json: bool = True,
        **kwargs: object,
    ) -> str | int | dict[str, object]:
        # Every Kelvin call, the token login included, passes through here; the client
        # re-raises network errors and timeouts unchanged, and a 5xx as ServerError.
        try:
            return await super().request(async_request_method, url, return_json, **kwargs)
        except (ServerError, httpx.TransportError) as exc:
            raise KelvinAPIUnavailableError() from exc


class SharedTokenSession(_KelvinSession):
    """A Kelvin session that reuses the service account's token across requests.

    Only the caching is ours: a miss delegates to the client, which is what
    knows how to mint one. Two requests missing at once mint twice and the
    later one wins, which costs what it costs today.
    """

    @async_property
    async def token(self) -> str:
        global _shared_token
        shared = _shared_token
        if shared is not None and shared.is_valid():
            return shared.value
        value = await super().token
        _shared_token = Token.from_str(value)
        return value

    @override
    async def request(
        self,
        async_request_method: Callable[..., Awaitable[httpx.Response]],
        url: str,
        return_json: bool = True,
        **kwargs: object,
    ) -> str | int | dict[str, object]:
        """Send once more with a fresh token when Kelvin refuses the shared one.

        `Token.is_valid` only looks at the expiry, so a token Kelvin stopped
        accepting - a restart with a new signing key - would otherwise be sent
        until it expires, failing every request of every worker for up to an
        hour. A 401 means Kelvin turned the request away before acting on it,
        so sending a write again does not apply it twice.
        """
        if "headers" in kwargs:
            # Only the login brings its own headers, and a 401 there is the
            # service account's password, which no fresh token fixes.
            return await super().request(async_request_method, url, return_json, **kwargs)
        # Outside the `try`: a 401 while minting is the login's.
        headers = await self.json_headers  # pyright: ignore[reportGeneralTypeIssues]
        try:
            return await super().request(
                async_request_method, url, return_json, headers=headers, **kwargs
            )
        except InvalidRequest as exc:
            if exc.status != HTTPStatus.UNAUTHORIZED:
                raise
        logger.debug("Kelvin refused the shared token; retrying once with a fresh one.", url=url)
        # A concurrent request may have minted a replacement already, and this
        # drops that one too, which costs one extra login.
        forget_shared_token()
        self._token = None
        headers = await self.json_headers  # pyright: ignore[reportGeneralTypeIssues]
        return await super().request(async_request_method, url, return_json, headers=headers, **kwargs)


# A whole selection travels as repeated ``name`` parameters in one request line,
# and that line is capped - apache's LimitRequestLine defaults to 8190 bytes and
# nothing in front of Kelvin raises it. Budgeted for the names alone, leaving the
# rest to the collection URL.
SEARCH_NAMES_BUDGET_BYTES = 6000


def name_chunks(identifiers: list[str]) -> Iterator[list[str]]:
    """Split ``identifiers`` into the largest groups that still fit one request line."""
    chunk: list[str] = []
    used = 0
    for identifier in identifiers:
        cost = len("&name=") + len(quote(identifier, safe=""))
        if chunk and used + cost > SEARCH_NAMES_BUDGET_BYTES:
            yield chunk
            chunk, used = [], 0
        chunk.append(identifier)
        used += cost
    if chunk:
        yield chunk


@dataclass
class KelvinPersistenceAdapterSettings:
    url: str = field(metadata={SETTINGS_NAME_METADATA: "kelvin_persistence_adapter.url"})
    username: str = field(metadata={SETTINGS_NAME_METADATA: "kelvin_persistence_adapter.username"})
    password: str = field(metadata={SETTINGS_NAME_METADATA: "kelvin_persistence_adapter.password"})


@dataclass
class _SessionHolder:
    """Mutable so the scope closes whatever an adapter put in it.

    Reading the ContextVar back in the scope's ``finally`` would not do: a value
    set deeper can land in a copied context and never reach it.
    """

    session: Session | None = None
    # Kelvin objects this request already fetched, by name.
    fetched: dict[str, object] = field(default_factory=dict)


_session_holder: ContextVar[_SessionHolder | None] = ContextVar("kelvin_session_holder", default=None)


@contextmanager
def enter_session_scope() -> Generator[_SessionHolder]:
    """Open a scope without closing what lands in it - the caller owns that."""
    holder = _SessionHolder()
    token = _session_holder.set(holder)
    try:
        yield holder
    finally:
        _session_holder.reset(token)


@asynccontextmanager
async def kelvin_session_scope() -> AsyncGenerator[None]:
    """Bind one Kelvin session to the work inside, then close it.

    Every adapter in the scope shares it, so a request opens one set of connections
    however many calls it makes, and no idle connection the server already closed
    carries to the next one. The login itself outlives the scope - see
    ``SharedTokenSession``.
    """
    with enter_session_scope() as holder:
        try:
            yield
        finally:
            if holder.session is not None:
                try:
                    await holder.session.close()
                except Exception:
                    # Raising here replaces an already-rendered response with a 500,
                    # and the connection this closes is going away either way.
                    logger.opt(exception=True).debug("Closing the Kelvin session failed.")


class KelvinPersistenceBaseAdapter(AsyncConfiguredAdapterMixin[KelvinPersistenceAdapterSettings], ABC):
    @classmethod
    @override
    def get_settings_cls(
        cls,
    ) -> Type[KelvinPersistenceAdapterSettings]:  # pragma: no cover
        return KelvinPersistenceAdapterSettings

    def __init__(self):
        self._settings = None

    @override
    async def configure(self, settings: KelvinPersistenceAdapterSettings):
        self._settings = settings

    @staticmethod
    def _session_holder_or_raise() -> _SessionHolder:
        holder = _session_holder.get()
        if holder is None:
            raise RuntimeError(
                "No Kelvin session scope is active. Wrap the work in "
                "`kelvin_session_scope()`; the UI router does this for every request."
            )
        return holder

    @property
    def fetched_this_request(self) -> dict[str, object]:
        """What this request has already read from Kelvin, so a write can skip a GET."""
        return self._session_holder_or_raise().fetched

    @property
    def kelvin_session(self) -> Session:
        """The session of the surrounding scope, opened on first use.

        Never stored on the adapter: adapters are process-wide singletons, so a
        session on one would outlive every request that shares it.
        """
        if self._settings is None:
            raise RuntimeError(
                "Something went wrong with the configuration of the "
                "KelvinPersistenceAdapter. No settings present."
            )
        holder = self._session_holder_or_raise()
        if holder.session is None:
            logger.trace(
                "Opening the request's Kelvin session.",
                adapter=type(self).__name__,
                kelvin_url=self._settings.url,
                kelvin_api_version=KELVIN_API_VERSION,
            )
            holder.session = SharedTokenSession(
                self._settings.username,
                self._settings.password,
                self._settings.url,
                api_version=KELVIN_API_VERSION,
                verify=os.environ.get("SSL_CERT_FILE"),
                timeout=KELVIN_TIMEOUT_SECONDS,
            )
            # `Session.client` raises "Session is closed." until this runs.
            holder.session.open()
        return holder.session


class _Named(Protocol):
    """A Kelvin object a group lookup keys by."""

    name: str


_N = TypeVar("_N", bound=_Named)


async def fetch_groups_by_name(
    search: Callable[[list[str]], AsyncIterator[_N]],
    names: list[str],
    kind: str,
    school: str,
) -> list[_N]:
    """The named groups of one school, in the order asked for, skipping what is gone.

    One search names a page of groups at once. Asking for more than one name
    needs a Kelvin whose v2 group collections take a repeated ``name``; an older
    one answers for the last value alone.
    """
    # Kelvin reads `*` in a name as a wildcard, so one arriving here would widen
    # the search rather than name a group. Dropped as the user search drops it.
    wanted = list(dict.fromkeys(name for name in names if name and "*" not in name))
    if not wanted:
        return []
    found: dict[str, _N] = {}
    for chunk in name_chunks(wanted):
        async for group in search(chunk):
            found[group.name] = group
    if missing := [name for name in wanted if name not in found]:
        # A deep link that outlived its group. The port promises to skip such a
        # name rather than fail.
        logger.debug("Skipped groups the school does not have.", kind=kind, school=school, names=missing)
    return [found[name] for name in names if name in found]
