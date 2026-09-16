# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from typing import cast
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from pytest_mock import MockerFixture
from ucsschool.kelvin.client import ServerError, Session

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
