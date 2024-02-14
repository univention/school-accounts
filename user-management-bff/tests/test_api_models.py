# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
from user_management_bff.api_models import ColumnConfig


class TestColumnConfig:
    def test_default_values(self):
        column_config = ColumnConfig(label="label", attribute="attr", order=0)
        assert column_config.sorting is None
        assert column_config.formatter is None
