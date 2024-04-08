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
from ..errors import CreationError, ObjectNotFoundError, OperationNotSupportedError
from ..lang import _
from ..models import User, UserAttributes
from ..ports import UsersPersistencePort
from .base import KelvinPersistenceBaseAdapter


class KelvinUsersPersistenceAdapter(UsersPersistencePort, KelvinPersistenceBaseAdapter):

    @staticmethod
    def _user_attribute_to_kelvin_attribute(attribute_name: str) -> str:
        MAPPING = {
            "last_name": "lastname",
            "first_name": "firstname",
            "username": "name",
        }
        return MAPPING.get(attribute_name, attribute_name)

    @staticmethod
    def _ensure_students_have_school_classes(user: User) -> None:
        if any((role for role in user.attributes.roles if role.startswith("student"))):
            for school in user.attributes.schools:
                if not user.attributes.school_classes.get(school, []):
                    raise OperationNotSupportedError(_("The user has to be in a school class."))

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
                school=user_create_request.school,
                schools=[user_create_request.school],
                school_classes={user_create_request.school: user_create_request.school_classes},
                roles=user_create_request.roles,
                disabled=not user_create_request.active,
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
                roles=[
                    f"{role}:school:{user_create_request.school}" for role in user_create_request.roles
                ],
            ),
        )

    async def delete_user(self, identifier: str) -> None:
        async with self.kelvin_session as session:
            try:
                kelvin_user = await UserResource(session=session).get(name=identifier)
                await kelvin_user.delete()
            except NoObject as exc:
                raise ObjectNotFoundError(identifier=identifier) from exc

    async def save_user(self, user: User) -> User:
        self._ensure_students_have_school_classes(user)
        async with self.kelvin_session as session:
            try:
                kelvin_user = await UserResource(session=session).get(name=user.id)
            except NoObject as exc:
                raise ObjectNotFoundError(identifier=user.id) from exc
            # The File adapter also excludes roles,
            # in order to mimic the behavior of the Kelvin adapter.
            # If this is updated, please also update the behavior in the File adapter.
            # Roles are excluded due to the fact that Kelvin is not able to properly handle
            # users with multiple roles.
            for key, value in user.attributes.model_dump(exclude={"roles"}).items():
                setattr(kelvin_user, self._user_attribute_to_kelvin_attribute(key), value)
            try:
                return self._user_from_kelvin_user(await kelvin_user.save())
            except InvalidRequest as exc:
                raise OperationNotSupportedError(exc.reason) from exc


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

    def _reload_data(self):
        with open(self.settings.source, "r") as fd:
            self._data = json.load(fd)

    async def configure(self, settings: FileUsersPersistenceAdapterSettings):
        self.settings = settings
        self._reload_data()

    async def get_users(self, school: str) -> list[User]:
        self._reload_data()
        return [
            User(id=user["id"], attributes=UserAttributes(**user["attributes"]))
            for user in self._data
            if school in user["attributes"]["schools"]
        ]

    async def get_user(self, identifier: str) -> User:
        self._reload_data()
        try:
            user = next(user for user in self._data if user["id"] == identifier)
            return User(id=user["id"], attributes=UserAttributes(**user["attributes"]))
        except StopIteration:
            raise ObjectNotFoundError(identifier=identifier)

    async def create_user(self, user_create_request: UserCreateRequest):
        new_roles = [f"{role}:school:{user_create_request.school}" for role in user_create_request.roles]
        self._data.append(
            {
                "id": user_create_request.username,
                "attributes": {
                    "last_name": user_create_request.last_name,
                    "first_name": user_create_request.first_name,
                    "username": user_create_request.username,
                    "password": user_create_request.password or None,
                    "roles": new_roles,
                    "schools": [user_create_request.school],
                    "school_classes": {user_create_request.school: user_create_request.school_classes},
                    "disabled": not user_create_request.active,
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
                roles=new_roles,
                schools=[user_create_request.school],
                school_classes={user_create_request.school: user_create_request.school_classes},
                disabled=not user_create_request.active,
            ),
        )

    async def delete_user(self, identifier: str) -> None:
        prev_users_count = len(self._data)
        self._data = [user for user in self._data if user["id"] != identifier]

        if len(self._data) == prev_users_count:
            raise ObjectNotFoundError(identifier=identifier)

        with open(self.settings.source, "w") as fd:
            json.dump(self._data, fd)

    async def save_user(self, user: User) -> User:
        for user_data in self._data:
            if user_data["id"] == user.id:
                # The Kelvin adapter currently does not update roles.
                # We'll mimic this behavior in the File adapter.
                updated_user = user.attributes.model_dump()
                del updated_user["roles"]
                user_data["attributes"].update(updated_user)
                with open(self.settings.source, "w") as fd:
                    json.dump(self._data, fd)
                return User(id=user_data["id"], attributes=UserAttributes(**user_data["attributes"]))
        raise ObjectNotFoundError(identifier=user.id)
