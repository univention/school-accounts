# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import json
from dataclasses import dataclass, field
from typing import Type

from port_loader import AsyncConfiguredAdapterMixin
from port_loader.models import SETTINGS_NAME_METADATA
from ucsschool.kelvin.client import InvalidRequest, NoObject, UserResource
from ucsschool.kelvin.client import User as KelvinUser

from ..api_models import UserCreateRequest
from ..errors import CreationError, ObjectNotFoundError
from ..models import User, UserAttributes
from ..ports import UsersPersistencePort
from .base import KelvinPersistenceBaseAdapter


class KelvinUsersPersistenceAdapter(UsersPersistencePort, KelvinPersistenceBaseAdapter):
    def _user_from_kelvin_user(self, kelvin_user: KelvinUser) -> User:
        return User(
            id=kelvin_user.name,
            attributes=UserAttributes(
                last_name=kelvin_user.lastname,
                first_name=kelvin_user.firstname,
                username=kelvin_user.name,
                disabled=kelvin_user.disabled,
                schools=kelvin_user.schools,
                school_classes=kelvin_user.school_classes,
                roles=kelvin_user.ucsschool_roles,
            ),
        )

    async def get_users(self, school: str) -> list[User]:
        async with self.kelvin_session as session:
            kelvin_users = UserResource(session=session).search(school=school)
            return [self._user_from_kelvin_user(kelvin_user) async for kelvin_user in kelvin_users]

    async def get_user(self, identifier: str) -> User:
        async with self.kelvin_session as session:
            try:
                kelvin_user = await UserResource(session=session).get(name=identifier)
                return self._user_from_kelvin_user(kelvin_user)
            except NoObject as exc:
                raise ObjectNotFoundError(identifier=identifier) from exc

    async def create_user(self, user_create_request: UserCreateRequest) -> User:
        async with self.kelvin_session as session:
            user = KelvinUser(
                name=user_create_request.username,
                firstname=user_create_request.first_name,
                lastname=user_create_request.last_name,
                school=user_create_request.schools[0],
                schools=user_create_request.schools,
                school_classes=user_create_request.school_classes,
                roles=user_create_request.roles,
                disabled=user_create_request.disabled,
                password=user_create_request.password,
                source_uid="ucsschool-user-management",
                record_uid=user_create_request.username,
                session=session,
            )
            try:
                await user.save()
            except (NoObject, InvalidRequest) as exc:
                raise CreationError(str(exc)) from exc

        return User(
            id=user.name,
            attributes=UserAttributes(
                last_name=user.lastname,
                first_name=user.firstname,
                username=user.name,
                disabled=user.disabled,
                schools=user.schools,
                school_classes=user.school_classes,
                roles=user.roles,
            ),
        )


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
        self.settings = settings
        with open(settings.source, "r") as fd:
            self._data = json.load(fd)

    async def get_users(self, school: str) -> list[User]:
        return [
            User(id=user["id"], attributes=UserAttributes(**user["attributes"]))
            for user in self._data
            if school in user["attributes"]["schools"]
        ]

    async def get_user(self, identifier: str) -> User:
        try:
            user = next(user for user in self._data if user["id"] == identifier)
            return User(id=user["id"], attributes=UserAttributes(**user["attributes"]))
        except StopIteration:
            raise ObjectNotFoundError(identifier=identifier)

    async def create_user(self, user_create_request: UserCreateRequest):
        self._data.append(
            {
                "id": user_create_request.username,
                "attributes": {
                    "last_name": user_create_request.last_name,
                    "first_name": user_create_request.first_name,
                    "username": user_create_request.username,
                    "roles": user_create_request.roles,
                    "schools": user_create_request.schools,
                    "school_classes": user_create_request.school_classes,
                    "activated": not user_create_request.disabled,
                },
            }
        )
        with open(self.settings.source, "w") as fd:
            json.dump(self._data, fd)

        return User(
            id=user_create_request.username,
            attributes=UserAttributes(
                last_name=user_create_request.last_name,
                first_name=user_create_request.first_name,
                username=user_create_request.username,
                roles=user_create_request.roles,
                schools=user_create_request.schools,
                school_classes=user_create_request.school_classes,
                disabled=user_create_request.disabled,
            ),
        )
