# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import json
import sys
from dataclasses import dataclass, field
from typing import Type

import aiofiles
from loguru import logger
from port_loader import AsyncConfiguredAdapterMixin
from port_loader.models import SETTINGS_NAME_METADATA
from ucsschool.kelvin.client import InvalidRequest, NoObject, UserResource
from ucsschool.kelvin.client import User as KelvinUser

from ..errors import ObjectNotFoundError, PasswordResetRejectedError
from ..models import User, UserAttributes
from ..ports import UsersPersistencePort
from .base import KelvinPersistenceBaseAdapter

if sys.version_info >= (3, 12):  # pragma: no cover
    from typing import override  # pyright: ignore[reportUnreachable]
else:
    from typing_extensions import override


def _safe_rejection_reason(raw: object) -> str:
    """Kelvin's ``InvalidRequest.reason`` is untyped (``resp_json['detail']`` as-is) - normalize
    whatever shape it has into the plain string ``PasswordResetRejectedError.message`` promises,
    since it flows straight into a rendered toast. Content is otherwise untouched (raw backend
    text, unbounded length) - a known limitation; replacing this with proper, translatable error
    codes is tracked in univention/dev/education/user-management#229."""
    if isinstance(raw, str):
        return raw
    try:
        return str(raw)
    except Exception as exc:
        logger.warning(
            "Could not convert Kelvin's rejection reason to a string.",
            raw_type=type(raw).__name__,
            error=exc,
        )
        return ""


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
                school_classes=kelvin_user.school_classes or {},
                work_groups=kelvin_user.workgroups or {},
                roles=kelvin_user.ucsschool_roles,
                legal_wards=kelvin_user.legal_wards,
                legal_guardians=kelvin_user.legal_guardians,
                email=kelvin_user.email,
                birthday=kelvin_user.birthday,
                expiration_date=kelvin_user.expiration_date,
            ),
        )

    async def get_users(
        self, school: str, school_classes: list[str] | None, work_groups: list[str] | None
    ) -> list[User]:
        # TODO dont filter here, let Kelvin filter by passing classes and workgroups to `.search` method
        async with self.kelvin_session as session:
            kelvin_users = UserResource(session=session).search(school=school)
            return [
                self._user_from_kelvin_user(kelvin_user)
                async for kelvin_user in kelvin_users
                if
                (
                    # No filtering
                    ((school_classes is None) and (work_groups is None))
                    # user is in a school class
                    or (
                        (school in kelvin_user.school_classes and school_classes is not None)
                        and any(
                            [
                                school_class in kelvin_user.school_classes[school]
                                for school_class in school_classes
                            ]
                        )
                    )
                    # user is in a workgroup
                    or (
                        (school in kelvin_user.workgroups and work_groups is not None)
                        and any(
                            [work_group in kelvin_user.workgroups[school] for work_group in work_groups]
                        )
                    )
                )
            ]

    async def get_user(self, identifier: str) -> User:
        async with self.kelvin_session as session:
            try:
                kelvin_user = await UserResource(session=session).get(name=identifier)
                return self._user_from_kelvin_user(kelvin_user)
            except NoObject as exc:
                logger.error("Unable to find user with the Kelvin API.", user_id=identifier)
                raise ObjectNotFoundError(identifier=identifier) from exc

    @override
    async def set_password(self, identifier: str, password: str) -> None:
        async with self.kelvin_session as session:
            try:
                kelvin_user = await UserResource(session=session).get(name=identifier)
            except NoObject as exc:
                logger.error("Unable to find user with the Kelvin API.", user_id=identifier)
                raise ObjectNotFoundError(identifier=identifier) from exc
            kelvin_user.password = password
            try:
                await kelvin_user.save()
            except InvalidRequest as exc:
                logger.error(
                    "Kelvin rejected the password change.", user_id=identifier, error=exc.reason
                )
                raise PasswordResetRejectedError(
                    identifier=identifier, message=_safe_rejection_reason(exc.reason)
                ) from exc


@dataclass
class FileUsersPersistenceAdapterSettings:
    source: str = field(metadata={SETTINGS_NAME_METADATA: "file_users_persistence_adapter.source"})


class FileUsersPersistenceAdapter(
    UsersPersistencePort, AsyncConfiguredAdapterMixin[FileUsersPersistenceAdapterSettings]
):
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

    async def _reload_data(self):
        async with aiofiles.open(self.settings.source, "r") as fd:
            self._data = json.loads(await fd.read())

    async def configure(self, settings: FileUsersPersistenceAdapterSettings):
        self.settings = settings
        await self._reload_data()

    async def get_users(
        self, school: str, school_classes: list[str] | None, work_groups: list[str] | None
    ) -> list[User]:
        await self._reload_data()
        if school_classes is None:
            school_classes = []
        if work_groups is None:
            work_groups = []
        data = [
            User(id=user["id"], attributes=UserAttributes(**user["attributes"]))
            for user in self._data
            if (
                school in user["attributes"]["schools"]
                and (
                    (not school_classes and not work_groups)
                    or (
                        any(
                            [
                                school_class in user["attributes"]["school_classes"][school]
                                for school_class in school_classes
                            ]
                        )
                        or (
                            school in user["attributes"]["work_groups"]
                            and any(
                                [
                                    work_group in user["attributes"]["work_groups"][school]
                                    for work_group in work_groups
                                ]
                            )
                        )
                    )
                )
            )
        ]
        return data

    async def get_user(self, identifier: str) -> User:
        await self._reload_data()
        try:
            user = next(user for user in self._data if user["id"] == identifier)
            return User(id=user["id"], attributes=UserAttributes(**user["attributes"]))
        except StopIteration:
            raise ObjectNotFoundError(identifier=identifier)

    @override
    async def set_password(self, identifier: str, password: str) -> None:
        await self._reload_data()
        for user_data in self._data:
            if user_data["id"] == identifier:
                user_data["attributes"]["password"] = password
                async with aiofiles.open(self.settings.source, "w") as fd:
                    await fd.write(json.dumps(self._data))
                return
        raise ObjectNotFoundError(identifier=identifier)
