# SPDX-FileCopyrightText: 2023-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import pytest

from user_management_bff.lang import _


@pytest.mark.parametrize(
    "lang,expected_translation",
    [("en", "Classes"), ("de", "Klassen"), (None, "Classes"), ("fr", "Classes")],
)
def test_translation_smoke_test(lang: str | None, expected_translation: str):
    translated = _("Classes", lang=lang)  # pyright: ignore[reportArgumentType]
    assert translated == expected_translation
