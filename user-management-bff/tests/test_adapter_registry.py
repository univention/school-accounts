# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
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
)
from user_management_bff.adapters.api import FastAPIUsersRepresentationAdapter
from user_management_bff.adapters.users import FileUsersPersistenceAdapter
from user_management_bff.ports import UsersPersistencePort, UsersRepresentationPort


class TestAdapterSelection:
    def test_correct_test_selection(self):
        selection = AdapterSelection()
        assert selection.users_persistence == FileUsersPersistenceAdapter
        assert selection.users_representation == FastAPIUsersRepresentationAdapter


@pytest.mark.parametrize(
    "port_cls,adapter_cls",
    [
        (AsyncAdapterSettingsProvider, EnvSettingsProvider),
        (UsersPersistencePort, FileUsersPersistenceAdapter),
        (UsersRepresentationPort, FastAPIUsersRepresentationAdapter),
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
