# SPDX-FileCopyrightText: 2023-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import pytest
from starlette.datastructures import Headers
from starlette.requests import Request

from user_management_bff.constants import DEFAULT_LANGUAGE
from user_management_bff.lang import N_, _, get_lang, lang_from_accept_header


@pytest.mark.parametrize(
    "lang,expected_translation",
    [("en", "Classes"), ("de", "Klassen"), (None, "Classes"), ("fr", "Classes")],
)
def test_translation_smoke_test(lang: str | None, expected_translation: str):
    translated = _("Classes", lang=lang)  # pyright: ignore[reportArgumentType]
    assert translated == expected_translation


def test_noop_marker_returns_the_literal_unchanged():
    assert N_("Student") == "Student"


@pytest.mark.parametrize(
    "header,expected",
    [
        ("de", "de"),
        ("de-DE", "de"),
        ("DE", "de"),
        ("de-DE,de;q=0.9,en;q=0.8", "de"),
        ("en-GB,en;q=0.9,de;q=0.8", "en"),
        # First tag unsupported, so the next supported one wins.
        ("fr,de;q=0.9", "de"),
        ("fr", DEFAULT_LANGUAGE),
        ("", DEFAULT_LANGUAGE),
        (",", DEFAULT_LANGUAGE),
    ],
)
def test_lang_from_accept_header(header: str, expected: str):
    assert lang_from_accept_header(header) == expected


def _request(headers: dict[str, str]) -> Request:
    return Request({"type": "http", "headers": Headers(headers).raw})


@pytest.mark.parametrize(
    "headers,expected",
    [
        ({"Accept-Language": "de"}, "de"),
        ({}, DEFAULT_LANGUAGE),
        ({"Accept-Language": ""}, DEFAULT_LANGUAGE),
    ],
)
def test_get_lang(headers: dict[str, str], expected: str):
    assert get_lang(_request(headers)) == expected
