# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import pytest

from user_management_bff.adapters.api import FastAPIUsersRepresentationAdapter
from user_management_bff.models import AttributeAccess, Permission


class TestFastAPIUsersRepresentationAdapter:
    @pytest.fixture()
    def adapter(self):
        return FastAPIUsersRepresentationAdapter()

    @pytest.mark.parametrize(
        "attribute_name,permissions,expected",
        [
            ("first_name", {Permission.read_first_name}, {"value": 1, "access": AttributeAccess.READ}),
            ("first_name", {Permission.write_first_name}, {"value": 1, "access": AttributeAccess.WRITE}),
            (
                "first_name",
                {Permission.read_first_name, Permission.write_first_name},
                {"value": 1, "access": AttributeAccess.WRITE},
            ),
            ("unknown", {}, {"value": None, "access": AttributeAccess.NONE}),
        ],
    )
    def test__get_attribute_dict(self, adapter, attribute_name, permissions, expected):
        assert adapter._get_attribute_dict(attribute_name, 1, permissions) == expected
