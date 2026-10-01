# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import datetime
import json
import os
from typing import TYPE_CHECKING, Any

import grpc
import pytest

# reportMissingTypeStubs (pyright) on the 4 imports below: cerbos ships these as implicit
# namespace packages (no __init__.py), so pyright can't confirm they're covered by cerbos/py.typed
# even though each has its own .pyi stub alongside the .py file.
from cerbos.effect.v1 import effect_pb2  # pyright: ignore[reportMissingTypeStubs]
from cerbos.engine.v1 import engine_pb2  # pyright: ignore[reportMissingTypeStubs]
from cerbos.request.v1 import request_pb2  # pyright: ignore[reportMissingTypeStubs]
from cerbos.response.v1 import response_pb2  # pyright: ignore[reportMissingTypeStubs]
from cerbos.sdk.model import CerbosTypeError
from google.protobuf import struct_pb2
from port_loader import EnvSettingsProvider

from ucsschool_accounts.adapters.permissions import (
    CerbosPermissionsAdapter,
    CerbosPermissionsAdapterSettings,
    FilePermissionsAdapter,
    FilePermissionsAdapterSettings,
    ucsschool_roles_to_cerbos_roles,
)
from ucsschool_accounts.constants import APP_NAME
from ucsschool_accounts.errors import PermissionsError
from ucsschool_accounts.models import (
    Permission,
    Target,
    TargetObject,
    TargetObjectType,
    User,
    UserAttributes,
)

if TYPE_CHECKING:
    from pathlib import Path
    from unittest.mock import AsyncMock

    from google.protobuf.internal.containers import MessageMap
    from pytest_mock import MockerFixture


def _struct_fields(attrs: dict[str, Any]) -> MessageMap[str, struct_pb2.Value]:
    struct = struct_pb2.Struct()
    struct.update(attrs)
    return struct.fields


@pytest.mark.parametrize(
    "role_strings,expected",
    [
        ([], []),
        (["a:b:c"], []),
        (["a:school:c"], [{"name": "a", "context": "c"}]),
        (["", "a:school:c", "d:e:f"], [{"name": "a", "context": "c"}]),
    ],
)
def test_ucsschool_roles_to_cerbos_roles(role_strings: list[str], expected: list[dict[str, str]]):
    assert ucsschool_roles_to_cerbos_roles(role_strings) == expected


@pytest.mark.asyncio
async def test_cerbos_permissions_adapter_settings_resolve_via_env_settings_provider(
    mocker: MockerFixture,
):
    # Regression test for univention/dev/libraries/port-loader#3: this module uses
    # `from __future__ import annotations`, so CerbosPermissionsAdapterSettings' fields only
    # resolve correctly if get_adapter_settings() resolves the deferred (PEP 563) annotations
    # back to real types instead of trusting dataclasses.Field.type raw.
    mocker.patch.dict(
        os.environ,
        {
            "CERBOS_PERMISSIONS_ADAPTER__CERBOS_TARGET": "cerbos.example.org:3593",
            "CERBOS_PERMISSIONS_ADAPTER__REQUEST_TIMEOUT": "20",
            "CERBOS_PERMISSIONS_ADAPTER__TLS_VERIFY": "0",
        },
    )
    settings = await EnvSettingsProvider().get_adapter_settings(CerbosPermissionsAdapterSettings)
    assert settings.cerbos_target == "cerbos.example.org:3593"
    assert settings.request_timeout == 20
    assert settings.tls_verify is False


class TestCerbosPermissionsAdapter:
    @pytest.fixture
    def adapter(self) -> CerbosPermissionsAdapter:
        return CerbosPermissionsAdapter()

    @pytest.fixture
    def settings(self) -> CerbosPermissionsAdapterSettings:
        return CerbosPermissionsAdapterSettings(
            cerbos_target="CERBOS_TARGET",
            request_timeout=10,
            tls_verify=False,
        )

    @pytest.fixture
    def configured_adapter(
        self, adapter: CerbosPermissionsAdapter, settings: CerbosPermissionsAdapterSettings
    ) -> CerbosPermissionsAdapter:
        adapter._settings = settings
        return adapter

    @pytest.fixture
    def user(self):
        return User(
            id="ID",
            attributes=UserAttributes(
                last_name="LN",
                first_name="FN",
                disabled=False,
                username="USERNAME",
                schools=[],
                roles=[],
                school_classes={},
                work_groups={},
            ),
        )

    def test_init_state(self, adapter: CerbosPermissionsAdapter):
        assert adapter._settings is None
        assert adapter._client is None

    @pytest.mark.parametrize(
        "attr,expected",
        [
            (1, 1),
            (True, True),
            ("a", "a"),
            (1.1, 1.1),
            (datetime.datetime(2000, 1, 1), "2000-01-01 00:00:00"),
            (datetime.date(2000, 1, 1), "2000-01-01"),
        ],
    )
    def test__sanitize_attr(
        self,
        adapter: CerbosPermissionsAdapter,
        attr: int | bool | str | float | datetime.datetime | datetime.date,
        expected: int | bool | str | float,
    ):
        assert adapter._sanitize_attr(attr) == expected

    @pytest.mark.parametrize(
        "user_data",
        [
            {
                "attributes": {
                    "disabled": False,
                    "first_name": "Dev",
                    "last_name": "User",
                    "roles": ["teacher:school:school1"],
                    "legal_wards": [],
                    "legal_guardians": [],
                    "school_classes": {"school1": ["1a", "2b"]},
                    "work_groups": {},
                    "schools": ["school1"],
                    "username": "dev",
                    "password": None,
                    "email": None,
                    "birthday": None,
                    "expiration_date": None,
                },
                "id": "dev",
            },
            {
                "attributes": {
                    "disabled": False,
                    "first_name": "firstname3",
                    "last_name": "lastname3",
                    "roles": ["teacher:school:test_school2", "student:school:test_school3", "a:b:c"],
                    "legal_wards": [],
                    "legal_guardians": [],
                    "school_classes": {"test_school1": ["1a", "2b"], "test_school2": ["3c"]},
                    "work_groups": {},
                    "schools": ["test_school2", "test_school3"],
                    "username": "firstname3.lastname3",
                    "password": None,
                    "email": None,
                    "birthday": None,
                    "expiration_date": None,
                },
                "id": "test_user3",
            },
        ],
    )
    def test__user_to_principal(self, adapter: CerbosPermissionsAdapter, user_data: dict[str, Any]):
        user = User(id=user_data["id"], attributes=UserAttributes(**user_data["attributes"]))
        expected = engine_pb2.Principal(
            id=user_data["id"],
            roles=["ucsschool:user"],
            attr=_struct_fields(
                {
                    "cerbos_roles": ucsschool_roles_to_cerbos_roles(user_data["attributes"]["roles"]),
                    "schools": user_data["attributes"]["schools"],
                    "school_classes": user_data["attributes"]["school_classes"],
                    "work_groups": user_data["attributes"]["work_groups"],
                }
            ),
        )
        assert adapter._user_to_principal(user) == expected

    @pytest.mark.parametrize(
        "target_obj,expected",
        [
            pytest.param(
                TargetObject(id="ID", attributes={}, type=TargetObjectType.SCHOOL),
                engine_pb2.Resource(
                    id="ID",
                    kind="ucsschool:school",
                    attr=_struct_fields(
                        {
                            "app_name": APP_NAME,
                            "old": {"cerbos_roles": [{"name": "school", "context": "ID"}]},
                        }
                    ),
                ),
                id="school_without_attributes",
            ),
            pytest.param(
                TargetObject(id="ID2", attributes={"1": 2}, type=TargetObjectType.SCHOOL),
                engine_pb2.Resource(
                    id="ID2",
                    kind="ucsschool:school",
                    attr=_struct_fields(
                        {
                            "app_name": APP_NAME,
                            "old": {"1": 2, "cerbos_roles": [{"name": "school", "context": "ID2"}]},
                        }
                    ),
                ),
                id="school_with_arbitrary_attribute",
            ),
            pytest.param(
                TargetObject(
                    id="ID3",
                    attributes={
                        "roles": ["teacher:school:school1", "student:school:school2"],
                        "schools": ["school1", "school2"],
                    },
                    type=TargetObjectType.USER,
                ),
                engine_pb2.Resource(
                    id="ID3",
                    kind="ucsschool:user",
                    attr=_struct_fields(
                        {
                            "app_name": APP_NAME,
                            "old": {
                                "roles": ["teacher:school:school1", "student:school:school2"],
                                "schools": ["school1", "school2"],
                                "cerbos_roles": [
                                    {"name": "teacher", "context": "school1"},
                                    {"name": "student", "context": "school2"},
                                ],
                            },
                        }
                    ),
                ),
                id="user_with_roles_and_schools",
            ),
            pytest.param(
                TargetObject(
                    id="ID4", attributes={"school": "school1"}, type=TargetObjectType.SCHOOL_CLASS
                ),
                engine_pb2.Resource(
                    id="ID4",
                    kind="ucsschool:class",
                    attr=_struct_fields(
                        {
                            "app_name": APP_NAME,
                            "old": {
                                "school": "school1",
                                "cerbos_roles": [{"name": "school_class", "context": "school1"}],
                            },
                        }
                    ),
                ),
                id="school_class",
            ),
            pytest.param(
                TargetObject(
                    id="ID5", attributes={"school": "school1"}, type=TargetObjectType.WORK_GROUP
                ),
                engine_pb2.Resource(
                    id="ID5",
                    kind="ucsschool:workgroup",
                    attr=_struct_fields(
                        {
                            "app_name": APP_NAME,
                            "old": {
                                "school": "school1",
                                "cerbos_roles": [{"name": "workgroup", "context": "school1"}],
                            },
                        }
                    ),
                ),
                id="work_group",
            ),
            pytest.param(
                TargetObject(
                    id="ID6",
                    attributes={"password": "secret", "roles": []},
                    type=TargetObjectType.USER,
                ),
                engine_pb2.Resource(
                    id="ID6",
                    kind="ucsschool:user",
                    attr=_struct_fields(
                        {"app_name": APP_NAME, "old": {"roles": [], "cerbos_roles": []}}
                    ),
                ),
                id="user_password_is_filtered_out",
            ),
            pytest.param(
                TargetObject(
                    id="ID7",
                    attributes={"password": "secret", "school": "school1"},
                    type=TargetObjectType.SCHOOL_CLASS,
                ),
                engine_pb2.Resource(
                    id="ID7",
                    kind="ucsschool:class",
                    attr=_struct_fields(
                        {
                            "app_name": APP_NAME,
                            "old": {
                                "password": "secret",
                                "school": "school1",
                                "cerbos_roles": [{"name": "school_class", "context": "school1"}],
                            },
                        }
                    ),
                ),
                id="password_is_not_sensitive_on_school_class",
            ),
        ],
    )
    def test__target_object_to_resource(
        self, adapter: CerbosPermissionsAdapter, target_obj: TargetObject, expected: engine_pb2.Resource
    ):
        assert adapter._target_object_to_resource(target_obj) == expected

    def test__resolve_target_object_old_only(self, adapter: CerbosPermissionsAdapter):
        target_object = TargetObject(id="ID", type=TargetObjectType.USER, attributes={})
        target = Target(old_target=target_object, new_target=None)
        assert adapter._resolve_target_object(target) is target_object

    def test__resolve_target_object_new_only(self, adapter: CerbosPermissionsAdapter):
        target_object = TargetObject(id="ID", type=TargetObjectType.USER, attributes={})
        target = Target(old_target=None, new_target=target_object)
        assert adapter._resolve_target_object(target) is target_object

    def test__resolve_target_object_both_identical(self, adapter: CerbosPermissionsAdapter):
        target_object = TargetObject(id="ID", type=TargetObjectType.USER, attributes={})
        target = Target(old_target=target_object, new_target=target_object)
        assert adapter._resolve_target_object(target) is target_object

    def test__resolve_target_object_both_none(self, adapter: CerbosPermissionsAdapter):
        target = Target(old_target=None, new_target=None)
        with pytest.raises(ValueError):
            adapter._resolve_target_object(target)

    @pytest.mark.parametrize(
        "response,expected",
        [
            (response_pb2.CheckResourcesResponse(request_id="RID", results=[]), {}),
            (
                response_pb2.CheckResourcesResponse(
                    request_id="RID",
                    results=[
                        response_pb2.CheckResourcesResponse.ResultEntry(
                            resource=response_pb2.CheckResourcesResponse.ResultEntry.Resource(
                                id="ID1", kind="ucsschool:user"
                            ),
                            actions={},
                        )
                    ],
                ),
                {"ID1": []},
            ),
            (
                response_pb2.CheckResourcesResponse(
                    request_id="RID",
                    results=[
                        response_pb2.CheckResourcesResponse.ResultEntry(
                            resource=response_pb2.CheckResourcesResponse.ResultEntry.Resource(
                                id="ID1", kind="ucsschool:user"
                            ),
                            actions={"read-first_name": effect_pb2.EFFECT_ALLOW},
                        )
                    ],
                ),
                {"ID1": [Permission.read_first_name]},
            ),
            (
                response_pb2.CheckResourcesResponse(
                    request_id="RID",
                    results=[
                        response_pb2.CheckResourcesResponse.ResultEntry(
                            resource=response_pb2.CheckResourcesResponse.ResultEntry.Resource(
                                id="ID1", kind="ucsschool:user"
                            ),
                            actions={"read-first_name": effect_pb2.EFFECT_DENY},
                        )
                    ],
                ),
                {"ID1": []},
            ),
        ],
    )
    def test__check_resources_response_to_permissions_dict(
        self,
        adapter: CerbosPermissionsAdapter,
        response: response_pb2.CheckResourcesResponse,
        expected: dict[str, list[Permission]],
    ):
        assert adapter._check_resources_response_to_permissions_dict(response) == expected

    @pytest.mark.parametrize(
        "item_count,size,expected_chunk_sizes",
        [
            (0, 50, []),
            (1, 50, [1]),
            (50, 50, [50]),
            (51, 50, [50, 1]),
            (100, 50, [50, 50]),
            (101, 50, [50, 50, 1]),
        ],
    )
    def test__chunked(
        self,
        adapter: CerbosPermissionsAdapter,
        item_count: int,
        size: int,
        expected_chunk_sizes: list[int],
    ):
        items = list(range(item_count))
        chunks = list(adapter._chunked(items, size))
        assert [len(chunk) for chunk in chunks] == expected_chunk_sizes
        assert [item for chunk in chunks for item in chunk] == items

    def test_settings_property(
        self, adapter: CerbosPermissionsAdapter, settings: CerbosPermissionsAdapterSettings
    ):
        with pytest.raises(
            RuntimeError,
            match="The settings should never be accessed before the adapter was configured!",
        ):
            _settings = adapter.settings
        adapter._settings = settings
        assert adapter.settings == settings

    def test_client(self, configured_adapter: CerbosPermissionsAdapter):
        assert configured_adapter._client is None
        assert configured_adapter.client is not None

    def test_get_settings_cls(self, adapter: CerbosPermissionsAdapter):
        assert adapter.get_settings_cls() == CerbosPermissionsAdapterSettings

    @pytest.mark.asyncio
    async def test_configure(
        self, adapter: CerbosPermissionsAdapter, settings: CerbosPermissionsAdapterSettings
    ):
        await adapter.configure(settings)
        assert adapter._settings == settings

    @pytest.mark.asyncio
    async def test_get_permissions_empty_targets(
        self, configured_adapter: CerbosPermissionsAdapter, user: User, mocker: MockerFixture
    ):
        client_mock: AsyncMock = mocker.AsyncMock()
        configured_adapter._client = client_mock
        result = await configured_adapter.get_permissions(user, [])
        assert result == {}
        client_mock.check_resources.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_permissions_request_err(
        self, configured_adapter: CerbosPermissionsAdapter, user: User, mocker: MockerFixture
    ):
        client_mock: AsyncMock = mocker.AsyncMock()
        client_mock.check_resources.side_effect = CerbosTypeError("MESSAGE")
        configured_adapter._client = client_mock
        target = Target(
            old_target=TargetObject(id="ID", type=TargetObjectType.SCHOOL, attributes={}),
            new_target=None,
        )
        with pytest.raises(PermissionsError, match="MESSAGE"):
            await configured_adapter.get_permissions(user, [target])

    @pytest.mark.asyncio
    async def test_get_permissions_transport_err(
        self, configured_adapter: CerbosPermissionsAdapter, user: User, mocker: MockerFixture
    ):
        client_mock: AsyncMock = mocker.AsyncMock()
        client_mock.check_resources.side_effect = grpc.aio.AioRpcError(
            grpc.StatusCode.UNAVAILABLE, grpc.aio.Metadata(), grpc.aio.Metadata(), details="MESSAGE"
        )
        configured_adapter._client = client_mock
        target = Target(
            old_target=TargetObject(id="ID", type=TargetObjectType.SCHOOL, attributes={}),
            new_target=None,
        )
        with pytest.raises(PermissionsError, match="MESSAGE"):
            await configured_adapter.get_permissions(user, [target])

    @pytest.mark.asyncio
    async def test_get_permissions(
        self, configured_adapter: CerbosPermissionsAdapter, user: User, mocker: MockerFixture
    ):
        client_mock: AsyncMock = mocker.AsyncMock()
        client_mock.check_resources.return_value = response_pb2.CheckResourcesResponse(
            request_id="RID",
            results=[
                response_pb2.CheckResourcesResponse.ResultEntry(
                    resource=response_pb2.CheckResourcesResponse.ResultEntry.Resource(
                        id="TID", kind="ucsschool:school"
                    ),
                    actions={"read-first_name": effect_pb2.EFFECT_ALLOW},
                )
            ],
        )
        configured_adapter._client = client_mock
        target_object = TargetObject(id="TID", type=TargetObjectType.SCHOOL, attributes={})
        target = Target(old_target=target_object, new_target=None)
        result = await configured_adapter.get_permissions(user, [target])
        assert result == {"TID": [Permission.read_first_name]}
        client_mock.check_resources.assert_called_once()
        call_kwargs = client_mock.check_resources.call_args.kwargs
        assert call_kwargs["principal"] == configured_adapter._user_to_principal(user)
        expected_resources = [
            request_pb2.CheckResourcesRequest.ResourceEntry(
                actions=[permission.value for permission in Permission],
                resource=configured_adapter._target_object_to_resource(target_object),
            )
        ]
        assert call_kwargs["resources"] == expected_resources

    @pytest.mark.asyncio
    async def test_get_permissions_batches_by_max_batch_size(
        self, configured_adapter: CerbosPermissionsAdapter, user: User, mocker: MockerFixture
    ):
        configured_adapter._settings = CerbosPermissionsAdapterSettings(
            cerbos_target="CERBOS_TARGET", request_timeout=10, tls_verify=False, max_batch_size=2
        )
        client_mock: AsyncMock = mocker.AsyncMock()

        def _response_for(target_ids: list[str]) -> response_pb2.CheckResourcesResponse:
            return response_pb2.CheckResourcesResponse(
                request_id="RID",
                results=[
                    response_pb2.CheckResourcesResponse.ResultEntry(
                        resource=response_pb2.CheckResourcesResponse.ResultEntry.Resource(
                            id=target_id, kind="ucsschool:school"
                        ),
                        actions={"read-first_name": effect_pb2.EFFECT_ALLOW},
                    )
                    for target_id in target_ids
                ],
            )

        client_mock.check_resources.side_effect = [
            _response_for(["T0", "T1"]),
            _response_for(["T2", "T3"]),
            _response_for(["T4"]),
        ]
        configured_adapter._client = client_mock
        targets = [
            Target(
                old_target=TargetObject(id=f"T{i}", type=TargetObjectType.SCHOOL, attributes={}),
                new_target=None,
            )
            for i in range(5)
        ]

        result = await configured_adapter.get_permissions(user, targets)

        assert result == {f"T{i}": [Permission.read_first_name] for i in range(5)}
        assert client_mock.check_resources.call_count == 3
        batch_sizes = [
            len(call.kwargs["resources"]) for call in client_mock.check_resources.call_args_list
        ]
        assert batch_sizes == [2, 2, 1]

    @pytest.mark.asyncio
    async def test_get_permissions_error_in_one_batch_still_attempts_all_batches(
        self, configured_adapter: CerbosPermissionsAdapter, user: User, mocker: MockerFixture
    ):
        configured_adapter._settings = CerbosPermissionsAdapterSettings(
            cerbos_target="CERBOS_TARGET", request_timeout=10, tls_verify=False, max_batch_size=2
        )
        client_mock: AsyncMock = mocker.AsyncMock()
        ok_response = response_pb2.CheckResourcesResponse(request_id="RID", results=[])
        client_mock.check_resources.side_effect = [
            ok_response,
            grpc.aio.AioRpcError(
                grpc.StatusCode.UNAVAILABLE, grpc.aio.Metadata(), grpc.aio.Metadata(), details="MESSAGE"
            ),
            ok_response,
        ]
        configured_adapter._client = client_mock
        targets = [
            Target(
                old_target=TargetObject(id=f"T{i}", type=TargetObjectType.SCHOOL, attributes={}),
                new_target=None,
            )
            for i in range(6)
        ]

        with pytest.raises(PermissionsError, match="MESSAGE"):
            await configured_adapter.get_permissions(user, targets)

        # Concurrent batches: every batch is attempted even though one of them fails.
        assert client_mock.check_resources.call_count == 3

    @pytest.mark.asyncio
    async def test_get_permissions_unexpected_exception_propagates_unwrapped(
        self, configured_adapter: CerbosPermissionsAdapter, user: User, mocker: MockerFixture
    ):
        client_mock: AsyncMock = mocker.AsyncMock()
        client_mock.check_resources.side_effect = ValueError("boom")
        configured_adapter._client = client_mock
        target = Target(
            old_target=TargetObject(id="ID", type=TargetObjectType.SCHOOL, attributes={}),
            new_target=None,
        )

        with pytest.raises(ValueError, match="boom"):
            await configured_adapter.get_permissions(user, [target])

    @pytest.mark.asyncio
    async def test_close_with_client(
        self, configured_adapter: CerbosPermissionsAdapter, mocker: MockerFixture
    ):
        client_mock: AsyncMock = mocker.AsyncMock()
        configured_adapter._client = client_mock
        await configured_adapter.close()
        client_mock.close.assert_awaited_once()
        assert configured_adapter._client is None

    @pytest.mark.asyncio
    async def test_close_no_client(self, adapter: CerbosPermissionsAdapter):
        assert adapter._client is None
        await adapter.close()
        assert adapter._client is None


class TestFilePermissionsAdapter:
    @pytest.fixture
    def adapter(self) -> FilePermissionsAdapter:
        return FilePermissionsAdapter()

    def test_get_settings_cls(self, adapter: FilePermissionsAdapter):
        assert adapter.get_settings_cls() == FilePermissionsAdapterSettings

    @pytest.mark.asyncio
    async def test_configure(self, adapter: FilePermissionsAdapter, tmp_path: Path):
        data_file = tmp_path / "test_data.json"
        data = {"foo": "bar"}
        with open(data_file, "w") as fd:
            json.dump(data, fd)
        await adapter.configure(FilePermissionsAdapterSettings(source=str(data_file)))
        assert adapter._data == data

    @pytest.mark.parametrize(
        "data,expected",
        [
            ({}, []),
            ({"ID": {"school": ["read-first_name"]}}, [Permission.read_first_name]),
            (
                {"ID": {"school": ["read-first_name", "unknown-permission"]}},
                [Permission.read_first_name],
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_get_permissions_for_schools(
        self,
        adapter: FilePermissionsAdapter,
        data: dict[str, dict[str, list[str]]],
        expected: list[Permission],
    ):
        adapter._data = data
        actor = User(
            id="ID",
            attributes=UserAttributes(
                first_name="Max",
                last_name="Mustermann",
                username="max.muster",
                disabled=False,
                schools=[],
                school_classes={},
                roles=[],
                work_groups={},
            ),
        )
        target_object1 = TargetObject(id="ID", type=TargetObjectType.SCHOOL, attributes={})
        target1 = Target(old_target=target_object1, new_target=None)
        result = await adapter.get_permissions(actor, [target1])
        assert result == {target_object1.id: expected}

        # same but with new_target
        target_object2 = TargetObject(id="ID", type=TargetObjectType.SCHOOL, attributes={})
        target2 = Target(old_target=None, new_target=target_object2)
        result = await adapter.get_permissions(actor, [target2])
        assert result == {target_object2.id: expected}
