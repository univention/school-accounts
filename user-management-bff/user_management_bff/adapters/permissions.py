# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import datetime
import json
from dataclasses import dataclass, field
from typing import TypeVar

from guardian_authz_client.client import GuardianAuthzClient
from guardian_authz_client.errors import GuardianAuthzClientError
from guardian_authz_client.models import (
    Actor,
    Context,
    GetPermissionsResult,
    GuardianObject,
    Namespace,
    Role,
)
from guardian_authz_client.models import Target as ClientTarget
from loguru import logger
from port_loader import AsyncConfiguredAdapterMixin
from port_loader.models import SETTINGS_NAME_METADATA
from typing_extensions import override

from ..constants import APP_NAME, NAMESPACE_NAME
from ..errors import PermissionsError
from ..models import (
    Permission,
    Target,
    TargetObject,
    TargetObjectAttributeValue,
    TargetObjectType,
    User,
)
from ..ports import PermissionsPort
from ..utils import get_oauth2_settings

_SanitizableAttr = TypeVar("_SanitizableAttr")


@dataclass
class GuardianPermissionsAdapterSettings:
    guardian_url: str = field(
        metadata={SETTINGS_NAME_METADATA: "guardian_permissions_adapter.guardian_url"}
    )
    oauth2_well_known_url: str = field(
        metadata={SETTINGS_NAME_METADATA: "guardian_permissions_adapter.oauth2_well_known_url"}
    )
    client_id: str = field(metadata={SETTINGS_NAME_METADATA: "guardian_permissions_adapter.client_id"})
    client_secret: str = field(
        default="", metadata={SETTINGS_NAME_METADATA: "guardian_permissions_adapter.client_secret"}
    )
    request_timeout: int = field(
        default=10, metadata={SETTINGS_NAME_METADATA: "guardian_permissions_adapter.request_timeout"}
    )


def ucsschool_roles_to_guardian_roles(role_strings: list[str]) -> list[Role]:
    return [
        Role(
            app_name=APP_NAME,
            namespace_name=NAMESPACE_NAME,
            name=role_parts[0],
            context=Context(app_name=APP_NAME, namespace_name=NAMESPACE_NAME, name=role_parts[2]),
        )
        for role in role_strings
        if role.count(":") == 2
        if (role_parts := role.split(":"))
        if role_parts[1] == "school"
    ]


class GuardianPermissionsAdapter(
    PermissionsPort, AsyncConfiguredAdapterMixin[GuardianPermissionsAdapterSettings]
):
    class Config:
        alias: str = "guardian"
        cached: bool = True

    def __init__(self):
        self._settings = None
        self._oauth2_settings = {}
        self._client = None

    @staticmethod
    def _sanitize_attr(attr: _SanitizableAttr) -> _SanitizableAttr | str:
        if isinstance(attr, datetime.datetime) or isinstance(attr, datetime.date):
            return str(attr)
        return attr

    @staticmethod
    def _user_to_actor(user: User) -> Actor:
        attribute_values: dict[str, TargetObjectAttributeValue] = user.attributes.model_dump()
        return Actor(
            id=user.id,
            roles=ucsschool_roles_to_guardian_roles(user.attributes.roles),
            attributes={
                key: GuardianPermissionsAdapter._sanitize_attr(value)
                for key, value in attribute_values.items()
            },
        )

    @staticmethod
    def _target_object_to_guardian_object(
        target_object: TargetObject | None,
    ) -> GuardianObject | None:
        if target_object is None:
            return None
        role_strings: list[str] = []
        if target_object.type == TargetObjectType.SCHOOL:
            role_strings = [f"school:school:{target_object.id}"]  # made up role, just for the Guardian
        elif target_object.type == TargetObjectType.SCHOOL_CLASS:
            role_strings = [f"school_class:school:{target_object.attributes['school']}"]
        elif target_object.type == TargetObjectType.WORK_GROUP:
            role_strings = [f"workgroup:school:{target_object.attributes['school']}"]
        elif target_object.type == TargetObjectType.USER:
            roles = target_object.attributes.get("roles", [])
            role_strings = roles if isinstance(roles, list) else []

        attributes: dict[str, TargetObjectAttributeValue] = {
            key: GuardianPermissionsAdapter._sanitize_attr(value)
            for key, value in target_object.attributes.items()
        }
        return GuardianObject(
            id=target_object.id,
            roles=ucsschool_roles_to_guardian_roles(role_strings),
            attributes=attributes,
        )

    @staticmethod
    def _permissions_result_to_permissions_dict(
        result: GetPermissionsResult,
    ) -> dict[str, list[Permission]]:
        permission_dict: dict[str, list[Permission]] = {}
        for target_permission in result.target_permissions:
            permission_dict[target_permission.target_id] = []
            for permission in target_permission.permissions:
                if permission.app_name == APP_NAME and permission.namespace_name == NAMESPACE_NAME:
                    try:
                        permission_dict[target_permission.target_id].append(Permission(permission.name))
                    except ValueError:
                        pass  # we do not care about unknown permissions and just skip them.
        return permission_dict

    @property
    def settings(self) -> GuardianPermissionsAdapterSettings:
        if self._settings is None:
            error_msg = "The settings should never be accessed before the adapter was configured!"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        return self._settings

    @property
    def client(self) -> GuardianAuthzClient:
        if self._client is None:
            self._client = GuardianAuthzClient(
                self.settings.guardian_url,
                self.settings.client_id,
                self._oauth2_settings["token_endpoint"],
                client_secret=self.settings.client_secret if self.settings.client_secret else None,
            )
        return self._client

    @classmethod
    @override
    def get_settings_cls(cls) -> type[GuardianPermissionsAdapterSettings]:
        return GuardianPermissionsAdapterSettings

    @override
    async def configure(self, settings: GuardianPermissionsAdapterSettings):
        self._settings = settings
        self._oauth2_settings = await get_oauth2_settings(
            settings.oauth2_well_known_url, settings.request_timeout
        )

    @override
    async def get_permissions(self, actor: User, targets: list[Target]) -> dict[str, list[Permission]]:
        try:
            result = await self.client.get_permissions(
                actor=self._user_to_actor(actor),
                targets=[
                    ClientTarget(
                        old_target=self._target_object_to_guardian_object(target.old_target),
                        new_target=self._target_object_to_guardian_object(target.new_target),
                    )
                    for target in targets
                ],
                namespaces=[Namespace(app_name=APP_NAME, name=NAMESPACE_NAME)],
            )
        except GuardianAuthzClientError as exc:
            logger.error(
                "Error fetching permissions for actor", actor_id=actor.id, error_message=exc.message
            )
            raise PermissionsError(exc.message) from exc
        return self._permissions_result_to_permissions_dict(result)


@dataclass
class FilePermissionsAdapterSettings:
    source: str = field(metadata={SETTINGS_NAME_METADATA: "file_permissions_adapter.source"})


class FilePermissionsAdapter(
    PermissionsPort, AsyncConfiguredAdapterMixin[FilePermissionsAdapterSettings]
):
    class Config:
        alias: str = "file"
        cached: bool = True

    def __init__(self):
        self._data = {}

    @classmethod
    @override
    def get_settings_cls(cls) -> type[FilePermissionsAdapterSettings]:
        return FilePermissionsAdapterSettings

    @override
    async def configure(self, settings: FilePermissionsAdapterSettings):
        with open(settings.source, "r") as fd:
            self._data = json.load(fd)

    @override
    async def get_permissions(self, actor: User, targets: list[Target]) -> dict[str, list[Permission]]:
        logger.debug("Fetching actor permissions from the Guardian", actor_id=actor.id)
        permission_data = {}
        for target in targets:
            if target.old_target:
                permission_data[target.old_target.id] = self._data.get(actor.id, {}).get(
                    target.old_target.type, []
                )
            elif target.new_target:
                permission_data[target.new_target.id] = self._data.get(actor.id, {}).get(
                    target.new_target.type, []
                )
        result = {}
        for target_id, permission_strings in permission_data.items():
            permissions = []
            for permission_string in permission_strings:
                try:
                    permissions.append(Permission(permission_string))
                except ValueError:
                    pass  # We do not care about unknown permissions. We just skip them.
            result[target_id] = permissions
        return result
