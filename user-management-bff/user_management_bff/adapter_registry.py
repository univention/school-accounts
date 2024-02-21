# Copyright (C) 2024 Univention GmbH
#
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
    SchoolsPersistencePort,
    SchoolsRepresentationPort,
    UsersPersistencePort,
    UsersRepresentationPort,
)

ADAPTER_REGISTRY: AsyncAdapterRegistry = lazy_object_proxy.Proxy(AsyncAdapterRegistry)
PORT_CLASSES = (
    UsersPersistencePort,
    UsersRepresentationPort,
    SchoolsPersistencePort,
    SchoolsRepresentationPort,
    FastAPIAuthenticationPort,
)


class AdapterSelection(BaseSettings):
    users_persistence: ImportString
    users_representation: ImportString
    schools_persistence: ImportString
    schools_representation: ImportString
    authentication: ImportString

    model_config = SettingsConfigDict(env_prefix="USER_MANAGEMENT__ADAPTER__")


def configure_registry(adapter_registry: AsyncAdapterRegistry):
    adapter_selection = AdapterSelection()
    adapter_registry.register_adapter(AsyncAdapterSettingsProvider, adapter_cls=EnvSettingsProvider)
    for port_cls, adapter_cls in [
        (UsersPersistencePort, adapter_selection.users_persistence),
        (UsersRepresentationPort, adapter_selection.users_representation),
        (SchoolsPersistencePort, adapter_selection.schools_persistence),
        (SchoolsRepresentationPort, adapter_selection.schools_representation),
        (FastAPIAuthenticationPort, adapter_selection.authentication),
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
