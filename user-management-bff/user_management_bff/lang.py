# Copyright (C) 2023 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import gettext
import os
from functools import cache
from typing import cast

from fastapi import Request

from user_management_bff.constants import APP_NAME, LANGUAGES, PROJECT_DIR


@cache
def gettext_instances() -> dict[str, gettext.GNUTranslations]:
    locales_dir = os.path.join(PROJECT_DIR, "locales")
    return {
        lang: cast(
            gettext.GNUTranslations,
            gettext.translation(APP_NAME, locales_dir, languages=[lang], fallback=True),
        )
        for lang in LANGUAGES
    }


@cache
def lang_from_accept_header(header: str) -> str:
    return header.split(",", 1)[0].split("-", 1)[0] if header else "de"


def get_lang(request: Request) -> str:
    return lang_from_accept_header(request.headers.get("Accept-Language", "en"))


def _(s: str, lang: str = "en") -> str:
    if lang not in LANGUAGES:
        lang = "en"
    gi = gettext_instances()
    return gi[lang].gettext(s)
