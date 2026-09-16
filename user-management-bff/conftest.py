# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--base_url", action="store")
    parser.addoption("--cerbos_url", action="store")
    parser.addoption("--kelvin_url", action="store")
    parser.addoption("--frontend_username", action="store", default="dev")
    parser.addoption("--frontend_password", action="store", default="univention")
    parser.addoption("--frontend_school", action="store", default="Goethe-Gymnasium Berlin")
    parser.addoption("--frontend_listed_user", action="store", default="jonas.huber")
    parser.addoption("--kelvin_username", action="store", default="Administrator")
    parser.addoption("--kelvin_password", action="store", default="univention")
