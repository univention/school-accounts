# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
"""UI router.

Serves the server-rendered HTML/HTMX UI. Handlers call ``business_logic.*`` and
render Jinja templates (full pages + HTMX fragments). There is no JSON API.

All routes require an authenticated session via the ``current_actor`` dependency,
except the interactive-login routes (login / callback / logout), which establish
or tear down that session.
"""
from functools import partial

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import Response

from .adapter_registry import port_dep
from .constants import (
    AUTH_CALLBACK_PATH,
    AUTH_LOGIN_PATH,
    AUTH_LOGOUT_PATH,
    FRONTEND_PREFIX,
    TEMPLATES_DIR,
)
from .lang import _, get_lang
from .ports import FastAPIAuthenticationPort

templates = Jinja2Templates(directory=TEMPLATES_DIR)
# Build static asset URLs relative to the UI prefix (StaticFiles is mounted at
# ``{FRONTEND_PREFIX}/static`` in main.py).
templates.env.globals["static"] = lambda path: f"{FRONTEND_PREFIX}/static/{path}"

router = APIRouter(prefix=FRONTEND_PREFIX)

# Module-level dependency callable so tests can target it via
# ``app.dependency_overrides``.
auth_port = port_dep(FastAPIAuthenticationPort)


async def current_actor(request: Request, auth: FastAPIAuthenticationPort = Depends(auth_port)) -> str:
    """Resolve the authenticated actor id, or raise ``NotAuthenticatedError``."""
    return await auth.get_authenticated_id(request)


def render(request: Request, name: str, **context) -> HTMLResponse:
    """Render ``name`` with the request's language and translation helper bound.

    Templates can call ``{{ _("text") }}`` (translated into the request language)
    and read ``{{ lang }}``.
    """
    lang = get_lang(request)
    context.setdefault("lang", lang)
    context["_"] = partial(_, lang=lang)
    return templates.TemplateResponse(request, name, context)


@router.get(AUTH_LOGIN_PATH)
async def login(
    request: Request,
    next: str = "",
    auth: FastAPIAuthenticationPort = Depends(auth_port),
) -> Response:
    """Begin the interactive login: redirect to Keycloak (auth code + PKCE)."""
    return await auth.login_redirect(request, next)


@router.get(AUTH_CALLBACK_PATH)
async def auth_callback(
    request: Request, auth: FastAPIAuthenticationPort = Depends(auth_port)
) -> Response:
    """Handle the Keycloak redirect: create the session and set the cookie."""
    return await auth.complete_login(request)


@router.api_route(AUTH_LOGOUT_PATH, methods=["GET", "POST"])
async def logout(request: Request, auth: FastAPIAuthenticationPort = Depends(auth_port)) -> Response:
    """End the local session and redirect into Keycloak's RP-initiated logout."""
    return await auth.logout(request)


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def shell(request: Request, actor: str = Depends(current_actor)) -> HTMLResponse:
    """Serve the application shell (requires an authenticated session)."""
    return render(request, "base.html")
