# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
"""UI router.

Serves the server-rendered HTML/HTMX UI. Handlers call ``business_logic.*`` and
render Jinja templates (full pages + HTMX fragments). There is no JSON API.
"""
from functools import partial

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .constants import FRONTEND_PREFIX, TEMPLATES_DIR
from .lang import _, get_lang

templates = Jinja2Templates(directory=TEMPLATES_DIR)
# Build static asset URLs relative to the UI prefix (StaticFiles is mounted at
# ``{FRONTEND_PREFIX}/static`` in main.py).
templates.env.globals["static"] = lambda path: f"{FRONTEND_PREFIX}/static/{path}"

router = APIRouter(prefix=FRONTEND_PREFIX)


def render(request: Request, name: str, **context) -> HTMLResponse:
    """Render ``name`` with the request's language and translation helper bound.

    Templates can call ``{{ _("text") }}`` (translated into the request language)
    and read ``{{ lang }}``.
    """
    lang = get_lang(request)
    context.setdefault("lang", lang)
    context["_"] = partial(_, lang=lang)
    return templates.TemplateResponse(request, name, context)


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def shell(request: Request) -> HTMLResponse:
    """Serve the application shell."""
    return render(request, "base.html")
