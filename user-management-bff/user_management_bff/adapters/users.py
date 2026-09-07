# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import asyncio
import sys
from dataclasses import dataclass, field
from typing import cast

import aiofiles
from loguru import logger
from port_loader import AsyncConfiguredAdapterMixin
from port_loader.models import SETTINGS_NAME_METADATA
from pydantic import TypeAdapter
from ucsschool.kelvin.client import InvalidRequest, NoObject, UserResource
from ucsschool.kelvin.client import User as KelvinUser

from ..errors import (
    ObjectNotFoundError,
    PasswordChangeOnNextLoginUnsupportedError,
    PasswordResetRejectedError,
)
from ..models import User, UserAttributes
from ..ports import UsersPersistencePort
from .base import KelvinPersistenceBaseAdapter

if sys.version_info >= (3, 12):  # pragma: no cover
    from typing import override  # pyright: ignore[reportUnreachable]
else:
    from typing_extensions import override


# The source file already holds the domain shape, so parse it as such instead of
# handing ``Any`` to every UserAttributes field.
_STORED_USERS = TypeAdapter(list[User])

# Kelvin forwards it only when listed in mapped_udm_properties.json
_UDM_CHANGE_ON_NEXT_LOGIN = "pwdChangeNextLogin"


def _udm_messages(raw: object) -> list[str]:
    """The ``msg`` of every entry in a UDM error payload, in order; empty for any other shape."""
    entries = cast("list[object]", raw) if isinstance(raw, list) else [raw]
    return [
        str(cast("dict[str, object]", entry)["msg"])
        for entry in entries
        if isinstance(entry, dict) and cast("dict[str, object]", entry).get("msg")
    ]


def _safe_rejection_reason(raw: object) -> str:
    """Normalize Kelvin's untyped ``InvalidRequest.reason`` into the plain string promised.

    Only UDM's ``msg`` entries survive; anything else is stringified whole, untouched.
    Stable error codes: user-management#231. Translating the text: #229."""
    if isinstance(raw, str):
        return raw
    if messages := _udm_messages(raw):
        return " ".join(messages)
    try:
        return str(raw)
    except Exception as exc:
        logger.warning(
            "Could not convert Kelvin's rejection reason to a string.",
            raw_type=type(raw).__name__,
            error=exc,
        )
        return ""


def _in_selected_group(
    school: str,
    school_classes: list[str],
    work_groups: list[str],
    user_classes: dict[str, list[str]],
    user_work_groups: dict[str, list[str]],
) -> bool:
    """Decide whether the group filter keeps a user of ``school``.

    No selection means no filter; otherwise membership in either list is enough.
    Shared by every ``UsersPersistencePort`` implementation so the adapters cannot
    drift apart on how they read the filter arguments again.
    """
    if not school_classes and not work_groups:
        return True
    return bool(
        set(school_classes).intersection(user_classes.get(school, ()))
        or set(work_groups).intersection(user_work_groups.get(school, ()))
    )


class KelvinUsersPersistenceAdapter(UsersPersistencePort, KelvinPersistenceBaseAdapter):
    _change_on_next_login_supported: bool = False

    @override
    def supports_password_change_on_next_login(self) -> bool:
        return self._change_on_next_login_supported

    def _user_from_kelvin_user(self, kelvin_user: KelvinUser) -> User:
        self._change_on_next_login_supported = _UDM_CHANGE_ON_NEXT_LOGIN in (
            kelvin_user.udm_properties or {}
        )
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
        self, school: str, school_classes: list[str], work_groups: list[str]
    ) -> list[User]:
        # TODO(ucsschool-kelvin-rest-api#149) dont filter here, let Kelvin filter by passing classes
        #   and workgroups to `.search` method
        async with self.kelvin_session as session:
            kelvin_users = UserResource(session=session).search(school=school)
            return [
                self._user_from_kelvin_user(kelvin_user)
                async for kelvin_user in kelvin_users
                if _in_selected_group(
                    school,
                    school_classes=school_classes,
                    work_groups=work_groups,
                    user_classes=kelvin_user.school_classes or {},
                    user_work_groups=kelvin_user.workgroups or {},
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
    async def set_password(
        self, identifier: str, password: str, change_on_next_login: bool = False
    ) -> None:
        async with self.kelvin_session as session:
            try:
                kelvin_user = await UserResource(session=session).get(name=identifier)
            except NoObject as exc:
                logger.error("Unable to find user with the Kelvin API.", user_id=identifier)
                raise ObjectNotFoundError(identifier=identifier) from exc
            if change_on_next_login and not self._change_on_next_login_supported:
                logger.warning(
                    "Kelvin does not map the property that forces a password change at "
                    "the next login, so this password was not reset. Add it to Kelvin's "
                    "mapped_udm_properties.json.",
                    user_id=identifier,
                    missing_udm_property=_UDM_CHANGE_ON_NEXT_LOGIN,
                    udm_properties=",".join(sorted(kelvin_user.udm_properties)),
                )
                raise PasswordChangeOnNextLoginUnsupportedError(identifier=identifier)
            kelvin_user.password = password
            if change_on_next_login:
                kelvin_user.udm_properties[_UDM_CHANGE_ON_NEXT_LOGIN] = True
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
        self._data: list[User] = []
        # "wb" truncates, so concurrent whole-file read-modify-writes raced.
        # Serialising is enough for a single-process dev/test stand-in.
        self._write_lock = asyncio.Lock()

    @classmethod
    def get_settings_cls(
        cls,
    ) -> type[FileUsersPersistenceAdapterSettings]:  # pragma: no cover
        return FileUsersPersistenceAdapterSettings

    async def _reload_data(self) -> None:
        async with aiofiles.open(self.settings.source, "rb") as fd:
            self._data = _STORED_USERS.validate_json(await fd.read())

    async def configure(self, settings: FileUsersPersistenceAdapterSettings):
        self.settings = settings
        await self._reload_data()

    async def get_users(
        self, school: str, school_classes: list[str], work_groups: list[str]
    ) -> list[User]:
        await self._reload_data()
        return [
            user
            for user in self._data
            if school in user.attributes.schools
            and _in_selected_group(
                school,
                school_classes=school_classes,
                work_groups=work_groups,
                user_classes=user.attributes.school_classes,
                user_work_groups=user.attributes.work_groups,
            )
        ]

    async def get_user(self, identifier: str) -> User:
        await self._reload_data()
        try:
            return next(user for user in self._data if user.id == identifier)
        except StopIteration:
            raise ObjectNotFoundError(identifier=identifier)

    @override
    def supports_password_change_on_next_login(self) -> bool:
        return True

    @override
    async def set_password(
        self, identifier: str, password: str, change_on_next_login: bool = False
    ) -> None:
        async with self._write_lock:
            await self._reload_data()
            for user in self._data:
                if user.id == identifier:
                    user.attributes.password = password
                    user.attributes.change_password_on_next_login = change_on_next_login
                    async with aiofiles.open(self.settings.source, "wb") as fd:
                        await fd.write(_STORED_USERS.dump_json(self._data))
                    return
        raise ObjectNotFoundError(identifier=identifier)
