# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import os
from contextlib import asynccontextmanager
from importlib import metadata

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles

from .adapter_registry import ADAPTER_REGISTRY, configure_registry, initialize_adapters
from .constants import API_PREFIX, CORS_ALLOWED_ORIGINS, FRONTEND_DIR, FRONTEND_PREFIX
from .errors import ObjectNotFoundError, OperationNotSupportedError, PermissionsError
from .logging import configure_logger
from .ports import FastAPIAuthenticationPort
from .routes import router


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
# FastAPI doesn't allow adding middleware after the app has been started,
# so unfortunately we can't put this in the lifespan to make use of the
# settings_port.
if CORS_ALLOWED_ORIGINS:
    origins = CORS_ALLOWED_ORIGINS.split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["Authorization"],
    )

# statically serve the frontend
if os.path.exists(FRONTEND_DIR):
    app.mount(FRONTEND_PREFIX, StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


@app.exception_handler(PermissionsError)
async def permissions_exception_handler(_request: Request, exc: PermissionsError):
    return ORJSONResponse(status_code=403, content={"detail": exc.message})


@app.exception_handler(OperationNotSupportedError)
async def operation_not_supported_exception_handler(_request: Request, exc: OperationNotSupportedError):
    return ORJSONResponse(status_code=400, content={"detail": exc.message})


@app.exception_handler(ObjectNotFoundError)
async def object_not_found_exception_handler(_request: Request, exc: ObjectNotFoundError):
    return ORJSONResponse(status_code=404, content={"detail": exc.message})


@app.get(f"{API_PREFIX}/config-app")
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
