# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import asyncio
import os
from abc import ABC
from collections.abc import AsyncGenerator, Awaitable, Callable, Generator
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Type, TypeVar

import httpx
from loguru import logger
from port_loader import AsyncConfiguredAdapterMixin
from port_loader.models import SETTINGS_NAME_METADATA
from typing_extensions import override
from ucsschool.kelvin.client import NoObject, ServerError, Session

from ..constants import GROUP_LOOKUP_MAX_CONCURRENCY
from ..errors import KelvinAPIUnavailableError

# this app supports the Kelvin v2 API only, so the version is pinned here.
# The client library still defaults to v1
KELVIN_API_VERSION = "v2"

# The client defaults to 10s, which a password write outruns: it runs the ucsschool
# import framework, far slower than an attribute change.
KELVIN_TIMEOUT_SECONDS = float(os.environ.get("USER_MANAGEMENT__KELVIN_TIMEOUT_SECONDS", "60"))

_T = TypeVar("_T")


async def fetch_each_by_name(
    fetch_one: Callable[[str], Awaitable[_T]], names: list[str], kind: str, school: str
) -> list[_T]:
    """Fetch each name concurrently, dropping the ones that no longer exist.

    Kelvin has no bulk lookup, so a set of specific groups is one request each.
    The semaphore is this call's own: it keeps a single school's lookups from
    becoming a burst, not the whole request's.
    """
    semaphore = asyncio.Semaphore(GROUP_LOOKUP_MAX_CONCURRENCY)

    async def _fetch(name: str) -> _T | None:
        async with semaphore:
            try:
                return await fetch_one(name)
            except NoObject:
                # Deleted between reading the user that references it and now.
                # The port promises to skip it rather than fail the whole list.
                logger.warning(
                    "Ignoring a group that no longer exists.", kind=kind, school=school, name=name
                )
                return None

    fetched = await asyncio.gather(*(_fetch(name) for name in names))
    return [group for group in fetched if group is not None]


@dataclass
class KelvinPersistenceAdapterSettings:
    url: str = field(metadata={SETTINGS_NAME_METADATA: "kelvin_persistence_adapter.url"})
    username: str = field(metadata={SETTINGS_NAME_METADATA: "kelvin_persistence_adapter.username"})
    password: str = field(metadata={SETTINGS_NAME_METADATA: "kelvin_persistence_adapter.password"})


class _KelvinSession(Session):
    @override
    async def request(
        self, async_request_method: object, url: str, return_json: bool = True, **kwargs: object
    ) -> str | int | dict[str, object]:
        # Every Kelvin call, the token login included, passes through here; the client
        # re-raises network errors and timeouts unchanged, and a 5xx as ServerError.
        try:
            return await super().request(async_request_method, url, return_json, **kwargs)
        except (ServerError, httpx.TransportError) as exc:
            raise KelvinAPIUnavailableError() from exc


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

    Every adapter in the scope shares it, so a request logs in once however many calls
    it makes, and no idle connection the server already closed carries to the next one.
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
            holder.session = _KelvinSession(
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
