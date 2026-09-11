# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import asyncio
import datetime
import json
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypeAlias, TypeVar, cast

import grpc

# reportMissingTypeStubs (pyright) on the 4 imports below: cerbos ships these as implicit
# namespace packages (no __init__.py), so pyright can't confirm they're covered by cerbos/py.typed
# even though each has its own .pyi stub alongside the .py file.
from cerbos.engine.v1 import engine_pb2  # pyright: ignore[reportMissingTypeStubs]
from cerbos.request.v1 import request_pb2  # pyright: ignore[reportMissingTypeStubs]
from cerbos.sdk.grpc.client import AsyncCerbosClient  # pyright: ignore[reportMissingTypeStubs]
from cerbos.sdk.grpc.utils import (  # pyright: ignore[reportMissingTypeStubs]
    is_allowed as cerbos_is_allowed,
)
from cerbos.sdk.model import CerbosTypeError
from google.protobuf import struct_pb2
from loguru import logger
from port_loader import AsyncClosableAdapterMixin, AsyncConfiguredAdapterMixin
from port_loader.models import SETTINGS_NAME_METADATA
from typing_extensions import override

from ..constants import APP_NAME
from ..errors import PermissionsError
from ..models import (
    Permission,
    TargetObjectAttributeValue,
    TargetObjectType,
)
from ..ports import PermissionsPort

if TYPE_CHECKING:
    from cerbos.response.v1.response_pb2 import CheckResourcesResponse
    from google.protobuf.internal.containers import MessageMap

    from ..models import Target, TargetObject, User

_PRINCIPAL_ROLE = "ucsschool:user"
_TARGET_OBJECT_TYPE_TO_KIND: dict[TargetObjectType, str] = {
    TargetObjectType.USER: "ucsschool:user",
    TargetObjectType.SCHOOL: "ucsschool:school",
    TargetObjectType.SCHOOL_CLASS: "ucsschool:class",
    TargetObjectType.WORK_GROUP: "ucsschool:workgroup",
}
# A list, not a set: gRPC's ResourceEntry.actions is an ordered repeated field, and building it
# from a set would give an arbitrary (hash-order-dependent) action order on every request.
_ALL_ACTIONS: list[str] = [permission.value for permission in Permission]

# The "old" resource attr dict holds sanitized TargetObject attribute values plus the
# synthesized cerbos_roles entry, which isn't a TargetObject attribute itself.
_TargetResourceAttrValue: TypeAlias = TargetObjectAttributeValue | list[dict[str, str]]

# What google.protobuf.struct_pb2.Struct.update() accepts, recursively - mirrors protobuf-internal
# well_known_types._StructValueArg, which isn't importable (private, leading-underscore name).
_StructValue: TypeAlias = (
    str | bool | int | float | None | Mapping[str, "_StructValue"] | Sequence["_StructValue"]
)

_SanitizableAttr = TypeVar("_SanitizableAttr")
_ChunkItem = TypeVar("_ChunkItem")


@dataclass
class CerbosPermissionsAdapterSettings:
    cerbos_target: str = field(
        metadata={SETTINGS_NAME_METADATA: "cerbos_permissions_adapter.cerbos_target"}
    )
    request_timeout: int = field(
        default=10, metadata={SETTINGS_NAME_METADATA: "cerbos_permissions_adapter.request_timeout"}
    )
    # Secure by default; environments with a plaintext Cerbos deployment override this
    # explicitly in their own config (see dev/.env.example).
    tls_verify: bool = field(
        default=True, metadata={SETTINGS_NAME_METADATA: "cerbos_permissions_adapter.tls_verify"}
    )
    # Cerbos rejects a CheckResources call outright if it carries more resources than the
    # server's own configured limit (50 in this deployment); keep this in sync with the
    # Cerbos server if that limit ever changes.
    max_batch_size: int = field(
        default=50, metadata={SETTINGS_NAME_METADATA: "cerbos_permissions_adapter.max_batch_size"}
    )


def ucsschool_roles_to_cerbos_roles(role_strings: list[str]) -> list[dict[str, str]]:
    return [
        {"name": role_parts[0], "context": role_parts[2]}
        for role in role_strings
        if role.count(":") == 2
        if (role_parts := role.split(":"))
        if role_parts[1] == "school"
    ]


class CerbosPermissionsAdapter(
    PermissionsPort,
    AsyncConfiguredAdapterMixin[CerbosPermissionsAdapterSettings],
    AsyncClosableAdapterMixin,
):
    class Config:
        alias: str = "cerbos"
        cached: bool = True

    def __init__(self):
        self._settings = None
        self._client = None

    @staticmethod
    def _sanitize_attr(attr: _SanitizableAttr) -> _SanitizableAttr | str:
        if isinstance(attr, datetime.datetime) or isinstance(attr, datetime.date):
            return str(attr)
        return attr

    @staticmethod
    def _role_strings_for_target_object(target_object: TargetObject) -> list[str]:
        if target_object.type == TargetObjectType.SCHOOL:
            return [f"school:school:{target_object.id}"]  # made up role, just for the policy
        elif target_object.type == TargetObjectType.SCHOOL_CLASS:
            return [f"school_class:school:{target_object.attributes['school']}"]
        elif target_object.type == TargetObjectType.WORK_GROUP:
            return [f"workgroup:school:{target_object.attributes['school']}"]
        roles = target_object.attributes.get("roles", [])  # USER
        return roles if isinstance(roles, list) else []

    @staticmethod
    def _resolve_target_object(target: Target) -> TargetObject:
        resolved = target.old_target if target.old_target is not None else target.new_target
        if resolved is None:
            raise ValueError("Target must have at least one of old_target/new_target set.")
        return resolved

    @staticmethod
    def _attrs_to_struct_fields(
        attrs: Mapping[str, _StructValue],
    ) -> MessageMap[str, struct_pb2.Value]:
        struct = struct_pb2.Struct()
        struct.update(attrs)
        return struct.fields

    @staticmethod
    def _user_to_principal(user: User) -> engine_pb2.Principal:
        cerbos_roles = ucsschool_roles_to_cerbos_roles(user.attributes.roles)
        if len(cerbos_roles) != len(user.attributes.roles):
            logger.debug(
                "Ignored actor role strings that are not <role>:school:<context>.",
                actor_id=user.id,
                roles=user.attributes.roles,
            )
        return engine_pb2.Principal(
            id=user.id,
            roles=[_PRINCIPAL_ROLE],
            attr=CerbosPermissionsAdapter._attrs_to_struct_fields(
                {
                    "cerbos_roles": cerbos_roles,
                    "schools": user.attributes.schools,
                    "school_classes": user.attributes.school_classes,
                    "work_groups": user.attributes.work_groups,
                }
            ),
        )

    @staticmethod
    def _target_object_to_resource(target_object: TargetObject) -> engine_pb2.Resource:
        """
        Convert a TargetObject to a Cerbos Resource, which is the wire format the Cerbos PDP
        understands. The Resource's "old" attribute is a dict of sanitized TargetObject
        attribute values plus a synthesized cerbos_roles entry, which isn't a TargetObject
        attribute itself.

        Sensitive attributes (TargetObjectType.sensitive_attributes) are omitted from the "old"
        dict, so they never leave this service and are never sent to Cerbos.
        """
        old: dict[str, _TargetResourceAttrValue] = {
            key: CerbosPermissionsAdapter._sanitize_attr(value)
            for key, value in target_object.attributes.items()
            if key not in target_object.type.sensitive_attributes
        }
        old["cerbos_roles"] = ucsschool_roles_to_cerbos_roles(
            CerbosPermissionsAdapter._role_strings_for_target_object(target_object)
        )
        return engine_pb2.Resource(
            id=target_object.id,
            kind=_TARGET_OBJECT_TYPE_TO_KIND[target_object.type],
            attr=CerbosPermissionsAdapter._attrs_to_struct_fields(
                # _TargetResourceAttrValue's datetime.date/datetime branch is unreachable here:
                # _sanitize_attr already replaced every date/datetime value in `old` with a str.
                cast("dict[str, _StructValue]", {"app_name": APP_NAME, "old": old})
            ),
        )

    @staticmethod
    def _check_resources_response_to_permissions_dict(
        response: CheckResourcesResponse,
    ) -> dict[str, list[Permission]]:
        return {
            result.resource.id: [
                permission for permission in Permission if cerbos_is_allowed(result, permission.value)
            ]
            for result in response.results
        }

    @staticmethod
    def _chunked(items: list[_ChunkItem], size: int) -> Iterator[list[_ChunkItem]]:
        return (items[start : start + size] for start in range(0, len(items), size))

    @property
    def settings(self) -> CerbosPermissionsAdapterSettings:
        if self._settings is None:
            error_msg = "The settings should never be accessed before the adapter was configured!"
            logger.critical(
                "The permissions backend is not configured, so no request can be authorized."
            )
            raise RuntimeError(error_msg)
        return self._settings

    @property
    def client(self) -> AsyncCerbosClient:
        if self._client is None:
            self._client = AsyncCerbosClient(
                self.settings.cerbos_target,
                timeout_secs=self.settings.request_timeout,
                tls_verify=self.settings.tls_verify,
            )
        return self._client

    @override
    @classmethod
    def get_settings_cls(cls) -> type[CerbosPermissionsAdapterSettings]:
        return CerbosPermissionsAdapterSettings

    @override
    async def configure(self, settings: CerbosPermissionsAdapterSettings):
        self._settings = settings

    @override
    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    @override
    async def get_permissions(self, actor: User, targets: list[Target]) -> dict[str, list[Permission]]:
        if not targets:
            return {}
        resources = [
            request_pb2.CheckResourcesRequest.ResourceEntry(
                actions=_ALL_ACTIONS,
                resource=self._target_object_to_resource(self._resolve_target_object(target)),
            )
            for target in targets
        ]
        principal = self._user_to_principal(actor)
        batches = list(self._chunked(resources, self.settings.max_batch_size))
        # return_exceptions=True: with several batches in flight concurrently, a systemic
        # failure (eg. Cerbos unreachable) fails every batch at once. Without this, gather
        # would propagate the first exception while the other batches' tasks keep running in
        # the background, and asyncio logs their eventual exceptions as "never retrieved" -
        # return_exceptions=True makes gather retrieve them all itself, so we can inspect and
        # handle them ourselves below instead of asyncio spraying noise into the logs.
        results = await asyncio.gather(
            *(self.client.check_resources(principal=principal, resources=batch) for batch in batches),
            return_exceptions=True,
        )
        permissions: dict[str, list[Permission]] = {}
        for result in results:
            if isinstance(result, (grpc.aio.AioRpcError, CerbosTypeError)):
                logger.error(
                    "Failed to ask Cerbos for permissions, so the request cannot be answered. "
                    "Check that the Cerbos service is running and reachable.",
                    actor_id=actor.id,
                    cerbos_target=self.settings.cerbos_target,
                    error_message=str(result),
                )
                raise PermissionsError(str(result)) from result
            if isinstance(result, BaseException):
                raise result
            # Only the join key is logged here, not any decision detail itself - Cerbos assigns
            # one call_id per check_resources call and reuses it for its own access/decision log
            # entries (see dev/docker-compose.yaml's audit.* flags), so this is enough to find the
            # full evaluation trace (matched policies, effective derived roles) there when needed.
            logger.debug(
                "Cerbos check completed - see Cerbos's own decision log for the full evaluation trace.",
                actor_id=actor.id,
                cerbos_call_id=result.cerbos_call_id,
            )
            permissions.update(self._check_resources_response_to_permissions_dict(result))
        logger.debug(
            "Checked permissions with Cerbos.",
            actor_id=actor.id,
            resource_count=len(resources),
            batch_count=len(batches),
            resolved_count=len(permissions),
        )
        return permissions


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
        self._data: dict[str, dict[str, list[str]]] = {}

    @override
    @classmethod
    def get_settings_cls(cls) -> type[FilePermissionsAdapterSettings]:
        return FilePermissionsAdapterSettings

    @override
    async def configure(self, settings: FilePermissionsAdapterSettings):
        with open(settings.source, "r") as fd:
            self._data = json.load(fd)
        logger.warning(
            "Authorization is not enforced by Cerbos: permissions come from a file. Outside "
            "development, select CerbosPermissionsAdapter instead.",
            source=settings.source,
            actor_count=len(self._data),
        )

    @override
    async def get_permissions(self, actor: User, targets: list[Target]) -> dict[str, list[Permission]]:
        logger.debug(
            "Reading actor permissions from the file adapter.",
            actor_id=actor.id,
            target_count=len(targets),
        )
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
