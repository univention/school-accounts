# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import json
import os
from dataclasses import dataclass, field
from typing import Optional, Type

from port_loader import AsyncConfiguredAdapterMixin
from port_loader.models import SETTINGS_NAME_METADATA
from ucsschool.kelvin.client import Session, UserResource
from ucsschool.kelvin.client import User as KelvinUser

from ..models import User, UserAttributes
from ..ports import UsersPersistencePort


@dataclass
class KelvinUsersPersistenceAdapterSettings:
    url: str = field(metadata={SETTINGS_NAME_METADATA: "kelvin_users_persistence_adapter.url"})
    username: str = field(metadata={SETTINGS_NAME_METADATA: "kelvin_users_persistence_adapter.username"})
    password: str = field(metadata={SETTINGS_NAME_METADATA: "kelvin_users_persistence_adapter.password"})


class KelvinUsersPersistenceAdapter(UsersPersistencePort, AsyncConfiguredAdapterMixin):
    @classmethod
    def get_settings_cls(
        cls,
    ) -> Type[KelvinUsersPersistenceAdapterSettings]:  # pragma: no cover
        return KelvinUsersPersistenceAdapterSettings

    def __init__(self):
        self._settings: Optional[KelvinUsersPersistenceAdapterSettings] = None

    def _user_from_kelvin_user(self, kelvin_user: KelvinUser) -> User:
        return User(
            id=kelvin_user.name,
            attributes=UserAttributes(
                last_name=kelvin_user.lastname,
                first_name=kelvin_user.firstname,
                username=kelvin_user.name,
                disabled=kelvin_user.disabled,
                schools=kelvin_user.schools,
                roles=kelvin_user.ucsschool_roles,
            ),
        )

    @property
    def kelvin_session(self) -> Session:
        if self._settings is None:
            raise RuntimeError(
                "Something went wrong with the configuration of the "
                "KelvinUsersPersistenceAdapter. No settings present."
            )
        return Session(
            self._settings.username,
            self._settings.password,
            self._settings.url,
            verify=os.environ.get("SSL_CERT_FILE"),
        )

    async def configure(self, settings: KelvinUsersPersistenceAdapterSettings):
        self._settings = settings

    async def get_users(self, school: str) -> list[User]:
        async with self.kelvin_session as session:
            kelvin_users = UserResource(session=session).search(school=school)
            return [self._user_from_kelvin_user(kelvin_user) async for kelvin_user in kelvin_users]


@dataclass
class FileUsersPersistenceAdapterSettings:
    source: str = field(metadata={SETTINGS_NAME_METADATA: "file_users_persistence_adapter.source"})


class FileUsersPersistenceAdapter(UsersPersistencePort, AsyncConfiguredAdapterMixin):
    class Config:
        alias = "file"
        cached = True

    def __init__(self):
        self._data = {}

    @classmethod
    def get_settings_cls(
        cls,
    ) -> Type[FileUsersPersistenceAdapterSettings]:  # pragma: no cover
        return FileUsersPersistenceAdapterSettings

    async def configure(self, settings: FileUsersPersistenceAdapterSettings):
        with open(settings.source, "r") as fd:
            self._data = json.load(fd)

    async def get_users(self, school: str) -> list[User]:
        return [
            User(id=user["id"], attributes=UserAttributes(**user["attributes"]))
            for user in self._data
            if school in user["attributes"]["schools"]
        ]
