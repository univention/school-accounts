# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import json

import pytest

from user_management_bff.adapters.permissions import (
    FilePermissionsAdapter,
    FilePermissionsAdapterSettings,
)
from user_management_bff.models import Permission, Target, TargetObject, User, UserAttributes


class TestFilePermissionsAdapter:
    @pytest.fixture
    def adapter(self):
        return FilePermissionsAdapter()

    def test_get_settings_cls(self, adapter):
        assert adapter.get_settings_cls() == FilePermissionsAdapterSettings

    @pytest.mark.asyncio
    async def test_configure(self, adapter, tmpdir):
        data_file = tmpdir / "test_data.json"
        data = {"foo": "bar"}
        with open(data_file, "w") as fd:
            json.dump(data, fd)
        await adapter.configure(FilePermissionsAdapterSettings(source=str(data_file)))
        assert adapter._data == data

    @pytest.mark.parametrize(
        "data,expected",
        [
            ({}, []),
            ({"ID": {"school": ["create-user"]}}, [Permission.create_user]),
            ({"ID": {"school": ["create-user", "unknown-permission"]}}, [Permission.create_user]),
        ],
    )
    @pytest.mark.asyncio
    async def test_get_permissions_for_schools(self, adapter, data, expected):
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
            ),
        )
        target1 = Target(old_target=TargetObject(id="ID", type="school", attributes={}), new_target=None)
        result = await adapter.get_permissions(actor, [target1])
        assert result == {target1.old_target.id: expected}
