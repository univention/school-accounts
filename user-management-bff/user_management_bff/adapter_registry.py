# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
from typing import Iterable, Optional, Type

import lazy_object_proxy
from port_loader import (
    AsyncAdapterRegistry,
    AsyncAdapterSettingsProvider,
    EnvSettingsProvider,
)
from pydantic import ImportString
from pydantic_settings import BaseSettings, SettingsConfigDict

from .ports import (
    FastAPIAuthenticationPort,
    PermissionsPort,
    SchoolClassesPersistencePort,
    SchoolsPersistencePort,
    SessionStorePort,
    UsersPersistencePort,
    WorkGroupsPersistencePort,
)

ADAPTER_REGISTRY: AsyncAdapterRegistry = lazy_object_proxy.Proxy(AsyncAdapterRegistry)
PORT_CLASSES = (
    UsersPersistencePort,
    SchoolsPersistencePort,
    SchoolClassesPersistencePort,
    WorkGroupsPersistencePort,
    FastAPIAuthenticationPort,
    SessionStorePort,
    PermissionsPort,
)


class AdapterSelection(BaseSettings):
    users_persistence: ImportString
    schools_persistence: ImportString
    school_classes_persistence: ImportString
    work_groups_persistence: ImportString
    authentication: ImportString
    session_store: ImportString
    permissions: ImportString

    model_config = SettingsConfigDict(env_prefix="USER_MANAGEMENT__ADAPTER__")


def configure_registry(adapter_registry: AsyncAdapterRegistry):
    adapter_selection = AdapterSelection()
    adapter_registry.register_adapter(AsyncAdapterSettingsProvider, adapter_cls=EnvSettingsProvider)
    for port_cls, adapter_cls in [
        (UsersPersistencePort, adapter_selection.users_persistence),
        (SchoolsPersistencePort, adapter_selection.schools_persistence),
        (SchoolClassesPersistencePort, adapter_selection.school_classes_persistence),
        (WorkGroupsPersistencePort, adapter_selection.work_groups_persistence),
        (FastAPIAuthenticationPort, adapter_selection.authentication),
        (SessionStorePort, adapter_selection.session_store),
        (PermissionsPort, adapter_selection.permissions),
    ]:
        adapter_registry.register_port(port_cls)
        adapter_registry.register_adapter(port_cls, adapter_cls=adapter_cls)


async def initialize_adapters(
    adapter_registry: AsyncAdapterRegistry, port_classes: Iterable[Type] = PORT_CLASSES
):
    for port_cls in port_classes:
        await adapter_registry(port_cls)


def port_dep(port_cls: Type, adapter_cls: Optional[Type] = None):
    async def _wrapper():
        return await ADAPTER_REGISTRY(port_cls, adapter_cls)

    return _wrapper
