# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import json
from dataclasses import dataclass, field
from typing import Optional, Type

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
from port_loader import AsyncConfiguredAdapterMixin
from port_loader.models import SETTINGS_NAME_METADATA

from ..constants import APP_NAME, NAMESPACE_NAME
from ..errors import PermissionsError
from ..models import Permission, Target, TargetObject, TargetObjectType, User
from ..ports import PermissionsPort
from ..utils import get_oauth2_settings


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


class GuardianPermissionsAdapter(PermissionsPort, AsyncConfiguredAdapterMixin):
    class Config:
        alias = "guardian"
        cached = True

    def __init__(self):
        self._settings = None
        self._oauth2_settings = {}
        self._client = None

    @staticmethod
    def _user_to_actor(user: User) -> Actor:
        return Actor(
            id=user.id,
            roles=ucsschool_roles_to_guardian_roles(user.attributes.roles),
            attributes=user.attributes.model_dump(),
        )

    @staticmethod
    def _target_object_to_guardian_object(
        target_object: Optional[TargetObject],
    ) -> Optional[GuardianObject]:
        if target_object is None:
            return None
        role_strings: list[str] = []
        if target_object.type == TargetObjectType.SCHOOL:
            role_strings = []
        elif target_object.type == TargetObjectType.USER:
            role_strings = target_object.attributes.get("roles", [])

        return GuardianObject(
            id=target_object.id,
            roles=ucsschool_roles_to_guardian_roles(role_strings),
            attributes=target_object.attributes,
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
            raise RuntimeError(
                "The settings should never be accessed before the adapter was configured!"
            )
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
    def get_settings_cls(cls) -> Type[GuardianPermissionsAdapterSettings]:
        return GuardianPermissionsAdapterSettings

    async def configure(self, settings: GuardianPermissionsAdapterSettings):
        self._settings = settings
        self._oauth2_settings = await get_oauth2_settings(
            settings.oauth2_well_known_url, settings.request_timeout
        )

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
            raise PermissionsError(exc.message) from exc
        return self._permissions_result_to_permissions_dict(result)


@dataclass
class FilePermissionsAdapterSettings:
    source: str = field(metadata={SETTINGS_NAME_METADATA: "file_permissions_adapter.source"})


class FilePermissionsAdapter(PermissionsPort, AsyncConfiguredAdapterMixin):
    class Config:
        alias = "file"
        cached = True

    def __init__(self):
        self._data = {}

    @classmethod
    def get_settings_cls(cls) -> Type[FilePermissionsAdapterSettings]:
        return FilePermissionsAdapterSettings

    async def configure(self, settings: FilePermissionsAdapterSettings):
        with open(settings.source, "r") as fd:
            self._data = json.load(fd)

    async def get_permissions(self, actor: User, targets: list[Target]) -> dict[str, list[Permission]]:
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
