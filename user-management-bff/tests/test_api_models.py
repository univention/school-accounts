# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import pytest
from pydantic import ValidationError

from user_management_bff.api_models import ColumnConfig, UserCreateRequest
from user_management_bff.models import Role


class TestColumnConfig:
    def test_default_values(self):
        column_config = ColumnConfig(label="label", attribute="attr", order=0)
        assert column_config.sorting is None
        assert column_config.formatter is None


class TestUserCreateRequest:

    def test_check_school_classes_for_student(self):
        UserCreateRequest(
            first_name="testuser",
            last_name="smith",
            username="testuser",
            password="testpassword",
            roles=[Role.TEACHER],
            disabled=False,
            school_classes=[],
            school="school1",
        )
        with pytest.raises(ValidationError) as e:
            UserCreateRequest(
                first_name="testuser",
                last_name="smith",
                username="testuser",
                password="testpassword",
                roles=[Role.STUDENT],
                disabled=False,
                school_classes=[],
                school="school1",
            )
        e.match("Value error, A student must have at least one school class.")
