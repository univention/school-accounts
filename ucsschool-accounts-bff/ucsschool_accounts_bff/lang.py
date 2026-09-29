# SPDX-FileCopyrightText: 2023-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import gettext
import os
from functools import cache

from fastapi import Request

from ucsschool_accounts_bff.constants import (
    APP_NAME,
    DEFAULT_LANGUAGE,
    LANGUAGES,
    PROJECT_DIR,
)


@cache
def gettext_instances() -> dict[str, gettext.NullTranslations]:
    locales_dir = os.path.join(PROJECT_DIR, "locales")
    return {
        lang: gettext.translation(APP_NAME, locales_dir, languages=[lang], fallback=True)
        for lang in LANGUAGES
    }


def lang_from_accept_header(header: str) -> str:
    """Return the first supported language the client asked for.

    Empty, absent and unsupported headers all resolve to ``DEFAULT_LANGUAGE``.
    The result is always in ``LANGUAGES``, so it is safe both as a catalog key
    and as ``<html lang>``. Quality values are ignored; tag order decides.
    """
    for tag in header.split(","):
        code = tag.split(";", 1)[0].strip().split("-", 1)[0].lower()
        if code in LANGUAGES:
            return code
    return DEFAULT_LANGUAGE


def get_lang(request: Request) -> str:
    return lang_from_accept_header(request.headers.get("Accept-Language", ""))


def _(s: str, lang: str = DEFAULT_LANGUAGE) -> str:
    if lang not in LANGUAGES:
        lang = DEFAULT_LANGUAGE
    gi = gettext_instances()
    return gi[lang].gettext(s)


def N_(s: str) -> str:
    """Mark a literal for extraction without translating it.

    For msgids only ever looked up through a variable, so that ``pybabel
    extract`` still sees the literal. gettext's conventional no-op marker.
    """
    return s
