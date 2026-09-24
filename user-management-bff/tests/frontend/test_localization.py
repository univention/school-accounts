# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import expect

if TYPE_CHECKING:
    from collections.abc import Callable

    from playwright.sync_api import Page

ENGLISH_HEADERS = ["Last name", "First name", "Username", "Roles"]
GERMAN_HEADERS = ["Nachname", "Vorname", "Benutzername", "Rollen"]


def _headers(page: Page) -> list[str]:
    # The design system upper-cases headers in CSS.
    return [header.inner_text().casefold() for header in page.locator("u-th").all()]


@pytest.mark.frontend
@pytest.mark.parametrize(
    ("language", "expected"),
    [("en-US", ENGLISH_HEADERS), ("de-DE", GERMAN_HEADERS)],
)
def test_the_language_follows_the_browser(
    open_in_language: Callable[[str], Page], language: str, expected: list[str]
) -> None:
    """L0006/L0009: the table headers follow the language the browser asks for."""
    page = open_in_language(language)

    assert [header.casefold() for header in expected] == _headers(page)[: len(expected)]


@pytest.mark.frontend
def test_an_unsupported_language_falls_back_to_english(
    open_in_language: Callable[[str], Page],
) -> None:
    """L0014: a browser language the module does not ship falls back to English."""
    page = open_in_language("fr-FR")

    assert [header.casefold() for header in ENGLISH_HEADERS] == _headers(page)[: len(ENGLISH_HEADERS)]


@pytest.mark.frontend
def test_role_names_are_localized(
    open_in_language: Callable[[str], Page], school: str, select_school: Callable[..., None]
) -> None:
    """L0011: role names are localized; the logged-in school admin's own row carries one."""
    page = open_in_language("de-DE")
    select_school(school, page=page)

    expect(page.locator("#results-region")).to_contain_text("Schuladmin")
