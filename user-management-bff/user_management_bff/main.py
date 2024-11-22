# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import os
from contextlib import asynccontextmanager
from importlib import metadata

from uuid import uuid4
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from .adapter_registry import ADAPTER_REGISTRY, configure_registry, initialize_adapters
from .constants import API_PREFIX, CORS_ALLOWED_ORIGINS, FRONTEND_DIR, FRONTEND_PREFIX
from .errors import (
    NotAuthenticatedError,
    ObjectNotFoundError,
    OperationNotSupportedError,
    PermissionsError,
)
from .lang import _, get_lang
from .logging import configure_logger
from .ports import FastAPIAuthenticationPort
from .routes import router
from loguru import logger
import loguru

from .correlation_id import correlation_id_ctx_var


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    await configure_logger()
    configure_registry(ADAPTER_REGISTRY)
    await initialize_adapters(ADAPTER_REGISTRY)
    auth_adapter = await ADAPTER_REGISTRY.request_port(FastAPIAuthenticationPort)
    fastapi_app.include_router(
        router, dependencies=[Depends(await auth_adapter.get_authentication_dependency())]
    )
    yield



app = FastAPI(
    lifespan=lifespan,
    title="UCS@school User Management BFF",
    version=metadata.version("user-management-bff"),
    openapi_url=f"{API_PREFIX}/openapi.json",
    docs_url=f"{API_PREFIX}/docs",
    default_response_class=ORJSONResponse,
    swagger_ui_oauth2_redirect_url=f"{API_PREFIX}/docs/oauth2-redirect",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
        "clientId": "ucsschool-user-management-ui",
        "scopes": ["openid"],
    },
)

CORRELATION_ID_HEADER_NAME = "X-Request-ID"

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
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



# statically serve the frontend
class StaticFilesSPA(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            response = await super().get_response(path, scope)
        except HTTPException:
            # serve the index.html for files not found
            return await super().get_response("index.html", scope)
        return response


if os.path.exists(FRONTEND_DIR):
    app.mount(
        FRONTEND_PREFIX, StaticFilesSPA(directory=FRONTEND_DIR, html=True), name="frontend"
    )  # pragma: no cover


@app.exception_handler(PermissionsError)
async def permissions_exception_handler(request: Request, exc: PermissionsError):
    lang = get_lang(request)
    return ORJSONResponse(
        status_code=403,
        content={"detail": _(exc.message, lang=lang), "missingPermissions": exc.missing_permissions},
    )


@app.exception_handler(OperationNotSupportedError)
async def operation_not_supported_exception_handler(request: Request, exc: OperationNotSupportedError):
    lang = get_lang(request)
    return ORJSONResponse(status_code=400, content={"detail": _(exc.message, lang=lang)})


@app.exception_handler(ObjectNotFoundError)
async def object_not_found_exception_handler(request: Request, exc: ObjectNotFoundError):
    lang = get_lang(request)
    detail = f"{_(exc.message, lang=lang)}: {exc.identifier}"
    return ORJSONResponse(status_code=404, content={"detail": detail})


@app.exception_handler(NotAuthenticatedError)
async def not_authenticated_exception_handler(request: Request, exc: NotAuthenticatedError):
    lang = get_lang(request)
    return ORJSONResponse(status_code=401, content={"detail": _(exc.message, lang=lang)})


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    lang = get_lang(request)
    errors = []
    for err in exc.errors():
        loc = err["loc"]
        if loc == ("body",):
            loc = (_("general", lang=lang),)
        errors.append(
            {
                "loc": loc,
                "msg": _(str(err.get("ctx", {}).get("error", None) or err["msg"]), lang=lang),
            }
        )
    return ORJSONResponse(status_code=422, content={"detail": errors})


@app.get(f"{API_PREFIX}/config/app")
def get_app_config() -> dict:
    """
    Returns the environment variables needed by the frontend to run the app.

    In production we run compiled javascript code in the frontend,
    which does not have access to environment variables that weren't present
    at compile time.
    Since we need AppCenter settings that are set at runtime,
    we work around this limitation by serving the variables as javascript,
    which is then fetched by the frontend's `UrlSettingsAdapter`.
    """
    return {key: value for key, value in os.environ.items() if key.startswith("VITE__")}
