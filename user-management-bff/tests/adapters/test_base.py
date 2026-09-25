# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import time
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import httpx
import jwt
import pytest
from async_property import async_property
from pytest_mock import MockerFixture
from ucsschool.kelvin.client import InvalidRequest, ServerError, Session

from user_management_bff.adapters import base as adapters_base
from user_management_bff.adapters.base import (
    KelvinPersistenceAdapterSettings,
    KelvinPersistenceBaseAdapter,
    kelvin_session_scope,
)
from user_management_bff.errors import KelvinAPIUnavailableError


class DummyAdapter(KelvinPersistenceBaseAdapter): ...


class TestKelvinPersistenceBaseAdapter:
    @pytest.fixture
    def adapter(self) -> DummyAdapter:
        return DummyAdapter()

    def test_get_settings_cls(self):
        assert KelvinPersistenceBaseAdapter.get_settings_cls() == KelvinPersistenceAdapterSettings

    @pytest.mark.asyncio
    async def test_configure(
        self, adapter: DummyAdapter, dummy_settings: KelvinPersistenceAdapterSettings
    ):
        await adapter.configure(dummy_settings)
        assert adapter._settings == dummy_settings

    def test_kelvin_session_no_settings(self, adapter: DummyAdapter):
        with pytest.raises(
            RuntimeError,
            match="Something went wrong with the configuration of the "
            "KelvinPersistenceAdapter. No settings present.",
        ):
            _session = adapter.kelvin_session

    def test_kelvin_session(
        self, adapter: DummyAdapter, dummy_settings: KelvinPersistenceAdapterSettings
    ):
        adapter._settings = dummy_settings
        assert adapter.kelvin_session.host == dummy_settings.url
        assert adapter.kelvin_session.username == dummy_settings.username
        assert adapter.kelvin_session.password == dummy_settings.password
        assert adapter.kelvin_session.api_version == "v2"

    def test_one_session_is_shared_by_every_adapter_in_the_scope(
        self, adapter: DummyAdapter, dummy_settings: KelvinPersistenceAdapterSettings
    ):
        """A session per call meant a login per call, which is what a bulk reset made
        expensive enough to take the proxy down."""
        other = DummyAdapter()
        adapter._settings = dummy_settings
        other._settings = dummy_settings
        assert adapter.kelvin_session is adapter.kelvin_session
        assert other.kelvin_session is adapter.kelvin_session
        assert adapter.kelvin_session.client is not None

    @pytest.mark.asyncio
    async def test_the_scope_closes_its_session_and_the_next_one_starts_fresh(
        self, adapter: DummyAdapter, dummy_settings: KelvinPersistenceAdapterSettings
    ):
        """Nothing is held between requests, so a connection the server dropped while
        idle cannot surface in the next one."""
        adapter._settings = dummy_settings
        async with kelvin_session_scope():
            first = adapter.kelvin_session
        with pytest.raises(RuntimeError, match="Session is closed."):
            _client = first.client

        async with kelvin_session_scope():
            assert adapter.kelvin_session is not first

    def test_no_session_outside_a_scope(
        self, adapter: DummyAdapter, dummy_settings: KelvinPersistenceAdapterSettings
    ):
        """Refused rather than silently opening one nobody closes."""
        adapter._settings = dummy_settings
        token = adapters_base._session_holder.set(None)
        try:
            with pytest.raises(RuntimeError, match="No Kelvin session scope is active"):
                _session = adapter.kelvin_session
        finally:
            adapters_base._session_holder.reset(token)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("failure", [ServerError("boom", status=500), httpx.ConnectTimeout("slow")])
    async def test_a_kelvin_that_does_not_answer_is_reported_as_unavailable(
        self,
        adapter: DummyAdapter,
        dummy_settings: KelvinPersistenceAdapterSettings,
        mocker: MockerFixture,
        failure: Exception,
    ):
        mocker.patch("ucsschool.kelvin.client.session.Session.request", side_effect=failure)
        adapter._settings = dummy_settings
        async with kelvin_session_scope():
            with pytest.raises(KelvinAPIUnavailableError):
                await adapter.kelvin_session.request(adapter.kelvin_session.client.get, "https://kelvin")


@pytest.mark.asyncio
async def test_the_scope_survives_a_session_that_cannot_be_closed():
    """The teardown runs after the response is rendered, so raising there would
    replace a good response with a 500."""
    session = MagicMock()
    session.close = AsyncMock(side_effect=RuntimeError("connection already gone"))

    async with kelvin_session_scope():
        holder = adapters_base._session_holder.get()
        assert holder is not None
        holder.session = cast("Session", cast("object", session))

    session.close.assert_awaited_once()


def _token_valid_for(seconds: int) -> str:
    """A JWT the Kelvin client will parse, expiring in ``seconds``."""
    return jwt.encode(
        {"exp": int(time.time()) + seconds}, "not-verified-anywhere-in-this-test", algorithm="HS256"
    )


@pytest.fixture
def no_shared_token(monkeypatch: pytest.MonkeyPatch):
    """The token outlives a request on purpose, so it must not outlive a test."""
    adapters_base.forget_shared_token()
    yield
    adapters_base.forget_shared_token()


@pytest.mark.asyncio
async def test_the_token_outlives_the_session_that_minted_it(
    no_shared_token, monkeypatch: pytest.MonkeyPatch
):
    """The client keeps its token on the session and a session lives for one
    request, so every page view was a password verification against LDAP."""
    minted: list[str] = []

    async def _mint(self: Session) -> str:
        minted.append("once")
        return _token_valid_for(3600)

    monkeypatch.setattr(Session, "token", async_property(_mint))

    first = adapters_base.SharedTokenSession("actor", "secret", "kelvin.test")
    second = adapters_base.SharedTokenSession("actor", "secret", "kelvin.test")
    assert await first.token == await second.token
    assert len(minted) == 1


def _kelvin(tokens: list[str], refused: set[str], seen: list[str]) -> httpx.MockTransport:
    """A Kelvin that hands out ``tokens`` in order and answers 401 to any in ``refused``."""
    minted = iter(tokens)

    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return httpx.Response(200, json={"access_token": next(minted)})
        token = request.headers["Authorization"].removeprefix("Bearer ")
        seen.append(token)
        if token in refused:
            return httpx.Response(401, json={"detail": "Could not validate credentials"})
        return httpx.Response(200, json={"name": "DEMOSCHOOL"})

    return httpx.MockTransport(handle)


@pytest.mark.asyncio
@pytest.mark.usefixtures("no_shared_token")
async def test_a_refused_shared_token_is_replaced_and_the_request_sent_again():
    """Kelvin restarting with a new signing key makes a cached token unusable,
    and the client cannot tell - it only checks the expiry."""
    stale, fresh = _token_valid_for(3600), _token_valid_for(3601)
    seen: list[str] = []
    transport = _kelvin([stale, fresh], refused={stale}, seen=seen)

    async with adapters_base.SharedTokenSession(
        "actor", "secret", "kelvin.test", transport=transport
    ) as session:
        assert await session.get("https://kelvin.test/schools/DEMOSCHOOL") == {"name": "DEMOSCHOOL"}

    assert seen == [stale, fresh]
    assert adapters_base._shared_token is not None
    assert adapters_base._shared_token.value == fresh


@pytest.mark.asyncio
@pytest.mark.usefixtures("no_shared_token")
async def test_a_fresh_token_that_is_refused_too_is_not_retried_again():
    """A second 401 is not a stale token, and retrying would never end."""
    first, second = _token_valid_for(3600), _token_valid_for(3601)
    seen: list[str] = []
    transport = _kelvin([first, second], refused={first, second}, seen=seen)

    async with adapters_base.SharedTokenSession(
        "actor", "secret", "kelvin.test", transport=transport
    ) as session:
        with pytest.raises(InvalidRequest) as exc_info:
            await session.get("https://kelvin.test/schools/DEMOSCHOOL")

    assert exc_info.value.status == 401
    assert seen == [first, second]


@pytest.mark.asyncio
@pytest.mark.usefixtures("no_shared_token")
async def test_other_client_errors_are_not_retried():
    seen: list[str] = []

    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return httpx.Response(200, json={"access_token": _token_valid_for(3600)})
        seen.append(request.url.path)
        return httpx.Response(403, json={"detail": "Forbidden"})

    transport = httpx.MockTransport(handle)
    async with adapters_base.SharedTokenSession(
        "actor", "secret", "kelvin.test", transport=transport
    ) as session:
        with pytest.raises(InvalidRequest) as exc_info:
            await session.get("https://kelvin.test/schools/DEMOSCHOOL")

    assert exc_info.value.status == 403
    assert len(seen) == 1


@pytest.mark.asyncio
@pytest.mark.usefixtures("no_shared_token")
async def test_a_refused_login_is_not_retried():
    """A 401 on the login is the service account's password; no fresh token fixes that."""
    logins: list[str] = []

    def handle(request: httpx.Request) -> httpx.Response:
        logins.append(request.url.path)
        return httpx.Response(401, json={"detail": "Incorrect username or password"})

    transport = httpx.MockTransport(handle)
    async with adapters_base.SharedTokenSession(
        "actor", "secret", "kelvin.test", transport=transport
    ) as session:
        with pytest.raises(InvalidRequest):
            await session.get("https://kelvin.test/schools/DEMOSCHOOL")

    assert len(logins) == 1


@pytest.mark.asyncio
async def test_an_expired_token_is_minted_again(no_shared_token, monkeypatch: pytest.MonkeyPatch):
    """Inside the window but past its own expiry is still no good."""
    minted: list[str] = []

    async def _mint(self: Session) -> str:
        minted.append("again")
        # Already past the client's leeway, so `Token.is_valid` refuses it.
        return _token_valid_for(-1)

    monkeypatch.setattr(Session, "token", async_property(_mint))

    session = adapters_base.SharedTokenSession("actor", "secret", "kelvin.test")
    await session.token
    await session.token

    assert len(minted) == 2
