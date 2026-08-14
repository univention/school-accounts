# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import os
from abc import ABC
from dataclasses import dataclass, field
from typing import Type

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
        if self._settings is None:
            raise RuntimeError(
                "Something went wrong with the configuration of the "
                "KelvinPersistenceAdapter. No settings present."
            )
        return Session(
            self._settings.username,
            self._settings.password,
            self._settings.url,
            api_version=KELVIN_API_VERSION,
            verify=os.environ.get("SSL_CERT_FILE"),
        )
