# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Shared plumbing for the adapter tests, and for the port contract tests.

A port contract test runs one matrix against *every* implementation of a port,
so that two adapters backing the same interface cannot drift apart. Issue #230
was exactly that drift: ``UsersPersistencePort`` declares ``list[str]``, both
adapters had widened themselves to ``list[str] | None``, and each then invented a
different sentinel for "no filter". The file adapter's reading was right, the
Kelvin adapter's was wrong, and every automated test path ran the file adapter.

Two rules the fakes here encode:

* **The Kelvin fake filters the way the real service does**, server-side
  (``?school=``, ``?name=``). The adapter is never credited with work Kelvin does
  for it, which is what makes the division of labor explicit: filtering by school
  is the data source's job, filtering by class and work group is the adapter's.
* **A contract test speaks only the port's own signature.** With plain lists, an
  empty list is the only way to express "no group filter" -- the very call the
  Kelvin adapter used to get wrong.
"""

from collections.abc import Iterator
from typing import Any, Callable
from unittest.mock import MagicMock

import pytest
from loguru import logger
from pytest_mock import MockerFixture

from user_management_bff.adapters.base import KelvinPersistenceAdapterSettings


@pytest.fixture
def dummy_settings() -> KelvinPersistenceAdapterSettings:
    return KelvinPersistenceAdapterSettings(url="https://test.com", username="test", password="password")


@pytest.fixture
def patch_kelvin_resource(
    monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
) -> Callable[[Any, str, Any], None]:
    """Replace ``<module>.<resource_name>`` with something yielding ``fake``.

    The adapters instantiate the Kelvin client's resource classes by name inside
    ``get_*``, so a test has to patch the name in the adapter's own module rather
    than the client package.
    """

    def _patch(module: Any, resource_name: str, fake: Any) -> None:
        monkeypatch.setattr(module, resource_name, mocker.MagicMock(return_value=fake))

    return _patch


@pytest.fixture
def make_kelvin_user_from_data(mocker: MockerFixture) -> Callable[[dict[str, Any]], MagicMock]:
    """Build a Kelvin client user from the dict shape the file adapter stores.

    One dataset can then drive both implementations of ``UsersPersistencePort``.
    """

    def _make_kelvin_user_from_data(user_data: dict[str, Any]) -> MagicMock:
        attributes = user_data["attributes"]
        kelvin_user = mocker.MagicMock()
        kelvin_user.name = user_data["id"]
        kelvin_user.lastname = attributes["last_name"]
        kelvin_user.firstname = attributes["first_name"]
        kelvin_user.schools = attributes["schools"]
        kelvin_user.school_classes = attributes["school_classes"]
        kelvin_user.workgroups = attributes["work_groups"]
        kelvin_user.ucsschool_roles = attributes["roles"]
        kelvin_user.disabled = attributes["disabled"]
        kelvin_user.legal_wards = attributes.get("legal_wards", [])
        kelvin_user.legal_guardians = attributes.get("legal_guardians", [])
        kelvin_user.email = attributes.get("email", None)
        kelvin_user.birthday = attributes.get("birthday", None)
        kelvin_user.expiration_date = attributes.get("expiration_date", None)
        return kelvin_user

    return _make_kelvin_user_from_data


@pytest.fixture
def make_kelvin_school_from_data(mocker: MockerFixture) -> Callable[[dict[str, str]], MagicMock]:
    """Build a Kelvin school from the dict shape the file adapter stores."""

    def _make_kelvin_school_from_data(school_data: dict[str, str]) -> MagicMock:
        kelvin_school = mocker.MagicMock()
        kelvin_school.name = school_data["id"]
        kelvin_school.display_name = school_data["display_name"]
        return kelvin_school

    return _make_kelvin_school_from_data


@pytest.fixture
def make_kelvin_group_from_data(mocker: MockerFixture) -> Callable[[str, str | None], MagicMock]:
    """Build a Kelvin school class / work group.

    ``description`` is what both group adapters fall back from when deriving a
    display name. The file format is ``{school: [name, ...]}`` with nowhere to put
    a description, so the contract datasets pass ``None`` here and assert the
    fallback; the description-present case stays in the Kelvin-only tests.
    """

    def _make_kelvin_group_from_data(name: str, description: str | None = None) -> MagicMock:
        kelvin_group = mocker.MagicMock()
        kelvin_group.name = name
        kelvin_group.description = description
        return kelvin_group

    return _make_kelvin_group_from_data


@pytest.fixture
def warning_records() -> Iterator[list[str]]:
    """Collect WARNING-and-above log lines, message plus bound ``extra`` fields.

    An adapter that silently drops part of a write has to say so in the log, so the
    log line is the assertion - including what it must *not* carry, like a password.
    """
    records: list[str] = []
    sink_id = logger.add(records.append, level="WARNING", format="{message} {extra}")
    try:
        yield records
    finally:
        logger.remove(sink_id)
