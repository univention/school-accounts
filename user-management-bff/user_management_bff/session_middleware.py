# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Delivery of a refreshed session cookie to the browser.

A ``Response`` injected into the authentication dependency cannot carry it: FastAPI
merges a dependency's sub-response headers only when the handler returns something
other than a ``Response``, and every route here returns one directly.

Pure ASGI rather than ``BaseHTTPMiddleware``, whose extra task drops coverage of
statements inside async route handlers - the test gate is 100% line coverage.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from starlette.requests import Request
from starlette.responses import Response

from .adapter_registry import ADAPTER_REGISTRY
from .ports import FastAPIAuthenticationPort

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Message, Receive, Scope, Send

_SET_COOKIE = b"set-cookie"


class SessionCookieMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app: ASGIApp = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_session_cookie(message: Message) -> None:
            if message["type"] == "http.response.start":
                scratch = Response()
                auth = cast(FastAPIAuthenticationPort, await ADAPTER_REGISTRY(FastAPIAuthenticationPort))
                await auth.apply_pending_session_cookie(Request(scope), scratch)
                cookies = [h for h in scratch.raw_headers if h[0] == _SET_COOKIE]
                headers = cast("list[tuple[bytes, bytes]]", message["headers"])
                message["headers"] = headers + cookies
            await send(message)

        await self.app(scope, receive, send_with_session_cookie)
