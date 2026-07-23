# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


def pytest_addoption(parser):
    parser.addoption("--base_url", action="store")
    parser.addoption("--guardian_management_url", action="store")
    parser.addoption("--kelvin_url", action="store")
