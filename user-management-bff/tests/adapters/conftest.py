# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Callable
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from user_management_bff.adapters.base import KelvinPersistenceAdapterSettings


@pytest.fixture
def dummy_settings() -> KelvinPersistenceAdapterSettings:
    return KelvinPersistenceAdapterSettings(url="https://test.com", username="test", password="password")


@pytest.fixture
def make_kelvin_school_from_data(mocker: MockerFixture) -> Callable[[dict[str, str]], MagicMock]:
    def _make_kelvin_school_from_data(school_data: dict[str, str]) -> MagicMock:
        kelvin_school = mocker.MagicMock()
        kelvin_school.name = school_data["id"]
        kelvin_school.description = school_data["display_name"]
        return kelvin_school

    return _make_kelvin_school_from_data
