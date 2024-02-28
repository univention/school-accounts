# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import json
from dataclasses import dataclass, field
from typing import Type

from port_loader import AsyncConfiguredAdapterMixin
from port_loader.models import SETTINGS_NAME_METADATA

from ..models import Permission, Target, User
from ..ports import PermissionsPort


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
        permission_data = {
            target.old_target.id: self._data.get(actor.id, {}).get(target.old_target.type, [])
            for target in targets
            if target.old_target
        }
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
