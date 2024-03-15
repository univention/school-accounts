# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import os
from abc import ABC
from dataclasses import dataclass, field
from typing import Type

from port_loader import AsyncConfiguredAdapterMixin
from port_loader.models import SETTINGS_NAME_METADATA
from ucsschool.kelvin.client import Session


@dataclass
class KelvinPersistenceAdapterSettings:
    url: str = field(metadata={SETTINGS_NAME_METADATA: "kelvin_persistence_adapter.url"})
    username: str = field(metadata={SETTINGS_NAME_METADATA: "kelvin_persistence_adapter.username"})
    password: str = field(metadata={SETTINGS_NAME_METADATA: "kelvin_persistence_adapter.password"})


class KelvinPersistenceBaseAdapter(AsyncConfiguredAdapterMixin, ABC):
    @classmethod
    def get_settings_cls(
        cls,
    ) -> Type[KelvinPersistenceAdapterSettings]:  # pragma: no cover
        return KelvinPersistenceAdapterSettings

    def __init__(self):
        self._settings = None

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
            verify=os.environ.get("SSL_CERT_FILE"),
        )
