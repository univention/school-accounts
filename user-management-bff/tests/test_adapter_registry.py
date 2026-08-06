# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
from typing import TYPE_CHECKING

import pytest
from port_loader import (
    AsyncAdapterRegistry,
    AsyncAdapterSettingsProvider,
    EnvSettingsProvider,
)

from user_management_bff.adapter_registry import (
    AdapterSelection,
    configure_registry,
    port_dep,
    shutdown_adapters,
)
from user_management_bff.adapters.session_store import InMemorySessionStoreAdapter
from user_management_bff.adapters.users import FileUsersPersistenceAdapter
from user_management_bff.ports import SessionStorePort, UsersPersistencePort

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


class TestAdapterSelection:
    def test_correct_test_selection(self):
        selection = AdapterSelection()
        assert selection.users_persistence == FileUsersPersistenceAdapter
        assert selection.session_store == InMemorySessionStoreAdapter


@pytest.mark.parametrize(
    "port_cls,adapter_cls",
    [
        (AsyncAdapterSettingsProvider, EnvSettingsProvider),
        (UsersPersistencePort, FileUsersPersistenceAdapter),
        (SessionStorePort, InMemorySessionStoreAdapter),
    ],
)
@pytest.mark.asyncio
async def test_configure_registry(port_cls, adapter_cls):
    registry = AsyncAdapterRegistry()
    configure_registry(registry)
    assert isinstance(await registry.request_port(port_cls), adapter_cls)


@pytest.mark.asyncio
async def test_port_dep(test_client):
    adapter = await port_dep(AsyncAdapterSettingsProvider)()
    assert isinstance(adapter, EnvSettingsProvider)


@pytest.mark.asyncio
async def test_shutdown_adapters_closes_adapters_that_define_close(mocker: "MockerFixture"):
    closable_adapter = mocker.AsyncMock()
    non_closable_adapter = mocker.Mock(spec=[])  # no `close` attribute at all
    registry = mocker.AsyncMock(side_effect=[closable_adapter, non_closable_adapter])

    await shutdown_adapters(registry, port_classes=[UsersPersistencePort, SessionStorePort])

    closable_adapter.close.assert_awaited_once()
