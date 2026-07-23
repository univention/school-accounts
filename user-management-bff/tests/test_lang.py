# SPDX-FileCopyrightText: 2023-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import pytest

from user_management_bff.lang import _


@pytest.mark.parametrize(
    "lang,expected_translation",
    [("en", "Classes"), ("de", "Klassen"), (None, "Classes"), ("fr", "Classes")],
)
def test_translation_smoke_test(lang, expected_translation):
    translated = _("Classes", lang=lang)
    assert translated == expected_translation
