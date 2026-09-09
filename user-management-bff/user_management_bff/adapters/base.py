# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import os
from abc import ABC
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Type

from loguru import logger
from port_loader import AsyncConfiguredAdapterMixin
from port_loader.models import SETTINGS_NAME_METADATA
from typing_extensions import override
from ucsschool.kelvin.client import Session

# this app supports the Kelvin v2 API only, so the version is pinned here.
# The client library still defaults to v1
KELVIN_API_VERSION = "v2"


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
        holder = _session_holder.get()
        if holder is None:
            raise RuntimeError(
                "No Kelvin session scope is active. Wrap the work in "
                "`kelvin_session_scope()`; the UI router does this for every request."
            )
        if holder.session is None:
            holder.session = Session(
                self._settings.username,
                self._settings.password,
                self._settings.url,
                api_version=KELVIN_API_VERSION,
                verify=os.environ.get("SSL_CERT_FILE"),
            )
            # `Session.client` raises "Session is closed." until this runs.
            holder.session.open()
        return holder.session
