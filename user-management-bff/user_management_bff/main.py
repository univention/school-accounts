# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
from contextlib import asynccontextmanager
from importlib import metadata
from urllib.parse import quote
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from loguru import logger
from port_loader import AsyncAdapterSettingsProvider
from starlette.middleware.base import RequestResponseEndpoint
from starlette.middleware.sessions import SessionMiddleware

from .adapter_registry import (
    ADAPTER_REGISTRY,
    configure_registry,
    initialize_adapters,
    shutdown_adapters,
)
from .constants import (
    AUTH_LOGIN_PATH,
    CORS_ALLOWED_ORIGINS,
    FRONTEND_PREFIX,
    SESSION_COOKIE_SECURE,
    SESSION_MIDDLEWARE_SECRET,
    STATIC_DIR,
)
from .correlation_id import correlation_id_ctx_var
from .errors import (
    NoSchoolUserError,
    NotAuthenticatedError,
    ObjectNotFoundError,
    PermissionsError,
)
from .lang import _, get_lang
from .logging import configure_logger
from .routes import render, router


@asynccontextmanager
async def lifespan(_fastapi_app: FastAPI):
    try:
        await configure_logger()
        configure_registry(ADAPTER_REGISTRY)

        settings_port: AsyncAdapterSettingsProvider = await ADAPTER_REGISTRY.request_port(
            AsyncAdapterSettingsProvider
        )
        await configure_logger(settings_port)

        await initialize_adapters(ADAPTER_REGISTRY)
    except Exception:
        import traceback

        traceback.print_exc()
    yield
    await shutdown_adapters(ADAPTER_REGISTRY)


app = FastAPI(
    lifespan=lifespan,
    title="UCS@school User Management",
    version=metadata.version("user-management-bff"),
    openapi_url=None,
    default_response_class=HTMLResponse,
)

CORRELATION_ID_HEADER_NAME = "X-Request-ID"


@app.middleware("http")
async def add_correlation_id(request: Request, call_next: RequestResponseEndpoint):
    """Add correlation id to request object and contextualize logger

    The contextualize method uses Python `contextvars` so the are unique to each thread/task.
    """

    correlation_id = request.headers.get(CORRELATION_ID_HEADER_NAME, str(uuid4()))
    correlation_id_ctx_var.set(correlation_id)

    with logger.contextualize(correlation_id=correlation_id):
        logger.trace(f"Setting correlation id for request {request.url} to {correlation_id}")
        response = await call_next(request)
        response.headers[CORRELATION_ID_HEADER_NAME] = correlation_id
        return response


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


# Holds the transient OAuth state (`state` + PKCE `code_verifier`) between the
# login redirect and the callback. The authenticated session itself lives
# server-side behind SessionStorePort, keyed by a separate signed cookie.
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_MIDDLEWARE_SECRET,
    same_site="lax",
    https_only=SESSION_COOKIE_SECURE,
)


# Serve the HTML/HTMX UI: vendored static assets + the UI router.
app.mount(f"{FRONTEND_PREFIX}/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(router)


# All error handlers render HTML: a toast for HTMX requests (retargeted at the
# shared toast region), a full-page message otherwise.
def _html_error(request: Request, message: str, status_code: int) -> Response:
    if request.headers.get("HX-Request") == "true":
        response = render(request, "fragments/toast.html", message=message, variant="error")
        response.headers["HX-Retarget"] = "#toast-region"
        response.headers["HX-Reswap"] = "beforeend"
        return response
    response = render(request, "pages/message.html", message=message)
    response.status_code = status_code
    return response


@app.exception_handler(PermissionsError)
async def permissions_exception_handler(request: Request, exc: PermissionsError):
    lang = get_lang(request)
    return _html_error(request, _(exc.message, lang=lang), 403)


# NoSchoolUserError subclasses PermissionsError; it keeps its own handler only so
# the message can differ, but the rendering is the same toast/message treatment.
@app.exception_handler(NoSchoolUserError)
async def no_school_user_exception_handler(request: Request, exc: NoSchoolUserError):
    return _html_error(request, exc.message, 403)


@app.exception_handler(ObjectNotFoundError)
async def object_not_found_exception_handler(request: Request, exc: ObjectNotFoundError):
    lang = get_lang(request)
    return _html_error(request, f"{_(exc.message, lang=lang)}: {exc.identifier}", 404)


@app.exception_handler(NotAuthenticatedError)
async def not_authenticated_exception_handler(request: Request, _exc: NotAuthenticatedError):
    # Send the browser into the interactive login, preserving where it was going.
    login_url = f"{FRONTEND_PREFIX}{AUTH_LOGIN_PATH}?next={quote(request.url.path)}"
    if request.headers.get("HX-Request") == "true":
        # htmx performs a client-side redirect when it sees this header.
        return Response(status_code=200, headers={"HX-Redirect": login_url})
    return RedirectResponse(login_url, status_code=303)


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, _exc: RequestValidationError):
    # Fallback for request validation failures (e.g. a missing query parameter).
    lang = get_lang(request)
    return _html_error(request, _("Invalid request.", lang=lang), 422)
