# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import pytest

from user_management_bff.adapters.base import (
    KelvinPersistenceAdapterSettings,
    KelvinPersistenceBaseAdapter,
)


class DummyAdapter(KelvinPersistenceBaseAdapter): ...


class TestKelvinPersistenceBaseAdapter:
    @pytest.fixture
    def adapter(self):
        return DummyAdapter()

    @pytest.fixture
    def dummy_settings(self):
        return KelvinPersistenceAdapterSettings(
            url="https://test.com", username="test", password="password"
        )

    def test_get_settings_cls(self):
        assert KelvinPersistenceBaseAdapter.get_settings_cls() == KelvinPersistenceAdapterSettings

    @pytest.mark.asyncio
    async def test_configure(self, adapter, dummy_settings):
        await adapter.configure(dummy_settings)
        assert adapter._settings == dummy_settings

    def test_kelvin_session_no_settings(self, adapter):
        with pytest.raises(
            RuntimeError,
            match="Something went wrong with the configuration of the "
            "KelvinPersistenceAdapter. No settings present.",
        ):
            _session = adapter.kelvin_session

    def test_kelvin_session(self, adapter, dummy_settings):
        adapter._settings = dummy_settings
        assert adapter.kelvin_session.host == dummy_settings.url
        assert adapter.kelvin_session.username == dummy_settings.username
        assert adapter.kelvin_session.password == dummy_settings.password
