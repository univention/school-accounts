# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import sys
from collections.abc import Callable, Coroutine
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

import pytest
from pytest_mock import MockerFixture
from starlette.requests import Request
from starlette.responses import Response

from ucsschool_accounts import session_middleware
from ucsschool_accounts.adapters.authentication import AlwaysAuthenticatedAdapter
from ucsschool_accounts.ports import FastAPIAuthenticationPort
from ucsschool_accounts.session_middleware import SessionCookieMiddleware

if sys.version_info >= (3, 12):
    from typing import override  # pyright: ignore[reportUnreachable]
else:
    from typing_extensions import override

if TYPE_CHECKING:
    from starlette.types import Message, Receive, Scope, Send

_UseAuth = Callable[[FastAPIAuthenticationPort], None]


class _CookieWritingAuth(FastAPIAuthenticationPort):
    def __init__(self, value: str | None) -> None:
        self._value: str | None = value

    @override
    async def get_authentication_dependency(self) -> Callable[..., Coroutine[Any, Any, str]]:
        raise NotImplementedError

    @override
    async def get_authenticated_id(self, request: Request) -> str:
        raise NotImplementedError

    @override
    async def apply_pending_session_cookie(self, request: Request, response: Response) -> None:
        assert isinstance(request, Request)
        if self._value is not None:
            response.set_cookie("session", self._value, path="/")


async def _ok_app(scope: Scope, receive: Receive, send: Send) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-type", b"text/html; charset=utf-8")],
        }
    )
    await send({"type": "http.response.body", "body": b"hi"})


async def _drive(app: Any, scope: Scope) -> list[Message]:
    sent: list[Message] = []

    async def receive() -> Message:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: Message) -> None:
        sent.append(message)

    await app(scope, receive, send)
    return sent


def _http_scope() -> Scope:
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "root_path": "",
        "headers": [],
        "client": ("127.0.0.1", 1234),
        "server": ("127.0.0.1", 80),
    }


def _cookies(messages: list[Message]) -> list[bytes]:
    start = next(m for m in messages if m["type"] == "http.response.start")
    return [value for name, value in start["headers"] if name == b"set-cookie"]


@pytest.fixture
def use_auth(mocker: MockerFixture) -> _UseAuth:
    def _use(adapter: FastAPIAuthenticationPort) -> None:
        mocker.patch.object(
            session_middleware, "ADAPTER_REGISTRY", mocker.AsyncMock(return_value=adapter)
        )

    return _use


@pytest.mark.asyncio
async def test_the_adapters_cookie_reaches_the_response(use_auth: _UseAuth):
    use_auth(_CookieWritingAuth("refreshed"))
    messages = await _drive(SessionCookieMiddleware(_ok_app), _http_scope())
    assert _cookies(messages) == [b"session=refreshed; Path=/; SameSite=lax"]


@pytest.mark.asyncio
async def test_the_responses_own_headers_survive(use_auth: _UseAuth):
    use_auth(_CookieWritingAuth("refreshed"))
    messages = await _drive(SessionCookieMiddleware(_ok_app), _http_scope())
    start = next(m for m in messages if m["type"] == "http.response.start")
    assert (b"content-type", b"text/html; charset=utf-8") in start["headers"]
    assert start["status"] == 200


@pytest.mark.asyncio
async def test_only_cookies_are_carried_over_from_the_scratch_response(use_auth: _UseAuth):
    use_auth(_CookieWritingAuth("refreshed"))
    messages = await _drive(SessionCookieMiddleware(_ok_app), _http_scope())
    start = next(m for m in messages if m["type"] == "http.response.start")
    assert [name for name, _ in start["headers"]].count(b"content-length") == 0


@pytest.mark.asyncio
async def test_a_request_that_touched_no_session_gets_no_cookie(use_auth: _UseAuth):
    use_auth(_CookieWritingAuth(None))
    messages = await _drive(SessionCookieMiddleware(_ok_app), _http_scope())
    assert _cookies(messages) == []


@pytest.mark.asyncio
async def test_the_default_adapter_writes_nothing(use_auth: _UseAuth):
    use_auth(AlwaysAuthenticatedAdapter())
    messages = await _drive(SessionCookieMiddleware(_ok_app), _http_scope())
    assert _cookies(messages) == []


@pytest.mark.asyncio
async def test_non_http_traffic_is_passed_straight_through(use_auth: _UseAuth):
    use_auth(_CookieWritingAuth("refreshed"))
    seen: list[Scope] = []

    async def _lifespan_app(scope: Scope, receive: Receive, send: Send) -> None:
        seen.append(scope)

    await _drive(SessionCookieMiddleware(_lifespan_app), {"type": "lifespan"})
    assert [scope["type"] for scope in seen] == ["lifespan"]


@pytest.mark.asyncio
async def test_the_refreshed_session_survives_a_direct_response(
    use_auth: _UseAuth, mocker: MockerFixture
):
    use_auth(_CookieWritingAuth("refreshed"))

    async def _redirecting_app(scope: Scope, receive: Receive, send: Send) -> None:
        response = Response(status_code=303, headers={"location": "/elsewhere"})
        await response(scope, receive, send)

    messages = await _drive(SessionCookieMiddleware(_redirecting_app), _http_scope())
    start = next(m for m in messages if m["type"] == "http.response.start")
    assert start["status"] == 303
    assert _cookies(messages) == [b"session=refreshed; Path=/; SameSite=lax"]


@pytest.mark.asyncio
async def test_the_adapter_sees_the_state_the_request_left_behind(use_auth: _UseAuth):
    captured: list[object] = []

    class _StateReadingAuth(_CookieWritingAuth):
        @override
        async def apply_pending_session_cookie(self, request: Request, response: Response) -> None:
            captured.append(getattr(request.state, "pending_session", "absent"))

    use_auth(_StateReadingAuth(None))
    now = datetime.now(timezone.utc)

    async def _stashing_app(scope: Scope, receive: Receive, send: Send) -> None:
        Request(scope).state.pending_session = now + timedelta(minutes=1)
        await _ok_app(scope, receive, send)

    await _drive(SessionCookieMiddleware(_stashing_app), _http_scope())
    assert captured == [now + timedelta(minutes=1)]
