# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

from contextlib import asynccontextmanager
from importlib import metadata
from typing import TYPE_CHECKING
from urllib.parse import quote, urlsplit, urlunsplit
from uuid import uuid4

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from loguru import logger
from port_loader import EnvSettingsProvider
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from .adapter_registry import ADAPTER_REGISTRY, configure_registry, initialize_adapters
from .constants import (
    AUTH_LOGIN_PATH,
    CORS_ALLOWED_ORIGINS,
    FRAME_ANCESTORS,
    FRONTEND_PREFIX,
    SESSION_COOKIE_PATH,
    SESSION_COOKIE_SECURE,
    SESSION_MIDDLEWARE_SECRET,
    STATIC_DIR,
)
from .correlation_id import correlation_id_ctx_var
from .errors import (
    KelvinAPIUnavailableError,
    NoSchoolUserError,
    NotAuthenticatedError,
    ObjectNotFoundError,
    PermissionsError,
)
from .lang import _, get_lang
from .logging import configure_logger
from .routes import render_static, router
from .session_middleware import SessionCookieMiddleware

if TYPE_CHECKING:
    from fastapi import Request
    from starlette.middleware.base import RequestResponseEndpoint


@asynccontextmanager
async def lifespan(_fastapi_app: FastAPI):
    try:
        await configure_logger(EnvSettingsProvider())
        configure_registry(ADAPTER_REGISTRY)
        await initialize_adapters(ADAPTER_REGISTRY)
    except Exception:
        logger.opt(exception=True).critical("Startup failed, so the application cannot serve requests.")
    else:
        logger.info("Application started.", version=metadata.version("ucsschool-accounts"))
    yield
    logger.info("Application shutting down.")
    await ADAPTER_REGISTRY.aclose()


app = FastAPI(
    lifespan=lifespan,
    title="School Accounts",
    version=metadata.version("ucsschool-accounts"),
    openapi_url=None,
    default_response_class=HTMLResponse,
)

CORRELATION_ID_HEADER_NAME = "X-Request-ID"
# Caps a client-supplied id, as echoed and logged in full. Fits upstream formats uncut
# (UUID 36, W3C `traceparent` 55), so they still match those systems' logs.
CORRELATION_ID_MAX_LENGTH = 64
CONTENT_SECURITY_POLICY = f"frame-ancestors {FRAME_ANCESTORS}"


# Added first so it runs inside the correlation-id middleware below.
app.add_middleware(SessionCookieMiddleware)


@app.middleware("http")
async def add_correlation_id(request: Request, call_next: RequestResponseEndpoint):
    """Add correlation id to request object and contextualize logger, and let the portal frame the UI

    The contextualize method uses Python `contextvars` so the are unique to each thread/task.
    """

    correlation_id = request.headers.get(CORRELATION_ID_HEADER_NAME, str(uuid4()))
    correlation_id = correlation_id[:CORRELATION_ID_MAX_LENGTH]
    correlation_id_ctx_var.set(correlation_id)

    with logger.contextualize(correlation_id=correlation_id):
        logger.trace("Handling request.", method=request.method, path=request.url.path)
        response = await call_next(request)
        response.headers[CORRELATION_ID_HEADER_NAME] = correlation_id
        response.headers["Content-Security-Policy"] = CONTENT_SECURITY_POLICY
        logger.trace("Handled request.", status_code=response.status_code)
        return response


# Holds the transient OAuth state (`state` + PKCE `code_verifier`) between the
# login redirect and the callback. The authenticated session itself lives in a
# separate, encrypted cookie owned by the authentication adapter.
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_MIDDLEWARE_SECRET,
    same_site="lax",
    https_only=SESSION_COOKIE_SECURE,
    path=SESSION_COOKIE_PATH,
)


# FastAPI doesn't allow adding middleware after the app has been started,
# so unfortunately we can't put this in the lifespan to make use of the
# settings_port.
if CORS_ALLOWED_ORIGINS:
    origins = CORS_ALLOWED_ORIGINS.split(",")  # pragma: no cover
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["Authorization", CORRELATION_ID_HEADER_NAME],
    )  # pragma: no cover


# Serve the HTML/HTMX UI: vendored static assets + the UI router.
app.mount(f"{FRONTEND_PREFIX}/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(router)


def _actor_id(request: Request) -> str | None:
    """The actor ``current_actor`` resolved, or None when the request failed before that."""
    actor_id = getattr(request.state, "actor_id", None)
    return actor_id if isinstance(actor_id, str) else None


# All error handlers render HTML: a toast for HTMX requests (retargeted at the
# shared toast region), a full-page message otherwise.
def _html_error(request: Request, message: str, status_code: int) -> Response:
    if request.headers.get("HX-Request") == "true":
        response = render_static(request, "fragments/toast.html", message=message, variant="error")
        response.headers["HX-Retarget"] = "#toast-region"
        response.headers["HX-Reswap"] = "beforeend"
        response.headers["HX-Reselect"] = "unset"
        return response
    response = render_static(request, "pages/message.html", message=message)
    response.status_code = status_code
    return response


@app.exception_handler(PermissionsError)
async def permissions_exception_handler(request: Request, exc: PermissionsError):
    lang = get_lang(request)
    return _html_error(request, _(exc.message, lang=lang), 403)


# NoSchoolUserError subclasses PermissionsError; it keeps its own handler only so
# the message can differ, but the rendering is the same toast/message treatment.
# No `_()` here, unlike its neighbours: this message embeds the offending user id,
# so it is translated and interpolated at the raise site.
@app.exception_handler(NoSchoolUserError)
async def no_school_user_exception_handler(request: Request, exc: NoSchoolUserError):
    return _html_error(request, exc.message, 403)


@app.exception_handler(ObjectNotFoundError)
async def object_not_found_exception_handler(request: Request, exc: ObjectNotFoundError):
    lang = get_lang(request)
    logger.info(
        "Request referenced an object that does not exist.",
        actor_id=_actor_id(request),
        path=request.url.path,
        identifier=exc.identifier,
    )
    return _html_error(request, f"{_(exc.message, lang=lang)}: {exc.identifier}", 404)


def _return_to(request: Request) -> str:
    """The page the login brings the browser back to.

    A plain GET is that page itself, filters included. An htmx request was sent from
    a page, and may fetch a bare fragment or POST to a route no GET answers. Only the
    path and query of that page are kept, and only one of this app's.
    """
    if request.method == "GET" and request.headers.get("HX-Request") != "true":
        return urlunsplit(("", "", request.url.path, request.url.query, ""))
    page = urlsplit(request.headers.get("HX-Current-URL") or "")
    if page.path.startswith(f"{FRONTEND_PREFIX}/"):
        return urlunsplit(("", "", page.path, page.query, ""))
    return f"{FRONTEND_PREFIX}/users"


@app.exception_handler(NotAuthenticatedError)
async def not_authenticated_exception_handler(request: Request, _exc: NotAuthenticatedError):
    # Send the browser into the interactive login, preserving where it was going.
    logger.debug("Redirecting an unauthenticated request to the login.", path=request.url.path)
    login_url = f"{FRONTEND_PREFIX}{AUTH_LOGIN_PATH}?next={quote(_return_to(request))}"
    if request.headers.get("HX-Request") == "true":
        # htmx performs a client-side redirect when it sees this header.
        return Response(status_code=200, headers={"HX-Redirect": login_url})
    return RedirectResponse(login_url, status_code=303)


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    # Fallback for request validation failures (e.g. a missing query parameter).
    lang = get_lang(request)
    logger.info(
        "Rejected a malformed request.",
        actor_id=_actor_id(request),
        path=request.url.path,
        errors=exc.errors(),
    )
    return _html_error(request, _("Invalid request.", lang=lang), 422)


# Starlette's class, not FastAPI's subclass: the router raises this one for a path no
# route matches (404) or a method the matching route does not answer (405). FastAPI's
# default handler would answer both with JSON, which the portal frame shows raw.
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    lang = get_lang(request)
    logger.info(
        "Rejected a request no route answers.",
        actor_id=_actor_id(request),
        method=request.method,
        path=request.url.path,
        status_code=exc.status_code,
    )
    if exc.status_code == 404:
        message = _("The requested page does not exist.", lang=lang)
    else:
        message = _("Invalid request.", lang=lang)
    response = _html_error(request, message, exc.status_code)
    # A 405 names the methods the route does answer in its Allow header.
    response.headers.update(exc.headers or {})
    return response


@app.exception_handler(KelvinAPIUnavailableError)
async def kelvin_api_unavailable_handler(request: Request, exc: KelvinAPIUnavailableError):
    logger.opt(exception=exc).error(
        "The user directory did not answer; the request could not be completed. Check that "
        "the Kelvin REST API is running and reachable from this host, and its log for this error.",
        actor_id=_actor_id(request),
        path=request.url.path,
    )
    lang = get_lang(request)
    return _html_error(
        request,
        _(
            "The user directory (Kelvin API) is currently unavailable. Please try again in a moment.",
            lang=lang,
        ),
        502,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, _exc: Exception):
    # Starlette re-raises after this, and uvicorn logs the traceback with the request id.
    lang = get_lang(request)
    response = _html_error(
        request, _("An unexpected error occurred. Please try again later.", lang=lang), 500
    )
    response.headers["Content-Security-Policy"] = CONTENT_SECURITY_POLICY
    if (correlation_id := correlation_id_ctx_var.get(None)) is not None:
        response.headers[CORRELATION_ID_HEADER_NAME] = correlation_id
    return response
