# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie
from unittest.mock import MagicMock

import httpx
import pytest
from authlib.integrations.starlette_client import OAuthError
from pytest_mock import MockerFixture
from starlette.datastructures import State
from starlette.responses import Response

from ucsschool_accounts.adapters.authentication import (
    AlwaysAuthenticatedAdapter,
    AlwaysAuthenticatedAdapterSettings,
    CookieSessionAuthenticationAdapter,
    CookieSessionAuthenticationAdapterSettings,
    NeverAuthenticatedAdapter,
)
from ucsschool_accounts.constants import FRONTEND_PREFIX, SESSION_COOKIE_PATH
from ucsschool_accounts.errors import NotAuthenticatedError
from ucsschool_accounts.models import SessionRecord


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _future() -> datetime:
    return _now() + timedelta(hours=1)


def _past() -> datetime:
    return _now() - timedelta(hours=1)


def _record(**overrides: object) -> SessionRecord:
    base = SessionRecord(
        actor_id="mina.teacher",
        display_name="Mina Teacher",
        sub="sub-1",
        kc_sid="kc-1",
        created_at=_now(),
        expires_at=_future(),
        refresh_token="rt",
        id_token="idt",
        csrf_token="csrf-token",
    )
    return base.model_copy(update=overrides)


def _set_cookie_header(response: Response) -> SimpleCookie:
    cookie = SimpleCookie()
    cookie.load(response.headers["set-cookie"])
    return cookie


def _cleared_paths(response: Response, name: str) -> set[str]:
    paths: set[str] = set()
    for key, value in response.raw_headers:
        if key != b"set-cookie":
            continue
        cookie = SimpleCookie()
        cookie.load(value.decode("latin-1"))
        morsel = cookie.get(name)
        if morsel is not None and not morsel.value:
            paths.add(morsel["path"])
    return paths


# The claims a refreshed ID token carries for the actor `_record` describes.
_CLAIMS = {"sub": "sub-1", "preferred_username": "mina.teacher"}


def _stub_refresh(
    mocker: MockerFixture,
    client: MagicMock,
    token: dict[str, object],
    claims: dict[str, object] | Exception | None = None,
) -> None:
    """Stub one refresh round-trip. An ``Exception`` for ``claims`` makes the ID token
    fail verification rather than come back with those claims."""
    client.fetch_access_token = mocker.AsyncMock(return_value=token)
    if isinstance(claims, Exception):
        client.parse_id_token = mocker.AsyncMock(side_effect=claims)
    else:
        client.parse_id_token = mocker.AsyncMock(return_value=_CLAIMS if claims is None else claims)


class TestCookieSessionAuthenticationAdapter:
    @pytest.fixture
    def settings(self) -> CookieSessionAuthenticationAdapterSettings:
        return CookieSessionAuthenticationAdapterSettings(
            well_known_url="https://kc/realms/ucs/.well-known/openid-configuration",
            client_id="ucsschool-accounts-ui",
            redirect_url="https://app/ui/auth/callback",
            cookie_secret="unit-test-secret",
            client_secret="unit-test-client-secret",
            post_logout_redirect_url="https://app/ui",
        )

    @pytest.fixture
    def adapter(
        self, settings: CookieSessionAuthenticationAdapterSettings
    ) -> CookieSessionAuthenticationAdapter:
        adapter = CookieSessionAuthenticationAdapter()
        adapter._settings = settings
        return adapter

    @pytest.fixture
    def client(self, mocker: MockerFixture) -> MagicMock:
        return mocker.MagicMock()

    @pytest.fixture
    def wired(
        self, adapter: CookieSessionAuthenticationAdapter, client: MagicMock
    ) -> CookieSessionAuthenticationAdapter:
        adapter._get_client = lambda: client
        return adapter

    def _request(
        self,
        mocker: MockerFixture,
        *,
        cookies: dict[str, str] | None = None,
        session: dict[str, str] | None = None,
    ) -> MagicMock:
        request = mocker.MagicMock()
        request.cookies = cookies if cookies is not None else {}
        request.session = session if session is not None else {}
        # A real State: on a mock, the pending-cookie handoff would resolve to a
        # mock attribute instead.
        request.state = State()
        return request

    def _cookie(
        self, adapter: CookieSessionAuthenticationAdapter, record: SessionRecord
    ) -> dict[str, str]:
        return {adapter.settings.cookie_name: adapter._cookie_codec.encode(record)}

    def _pending(self, request: MagicMock) -> object:
        return getattr(request.state, "pending_session", "absent")

    # --- settings / configuration -------------------------------------------------

    def test_get_settings_cls(self):
        assert (
            CookieSessionAuthenticationAdapter.get_settings_cls()
            == CookieSessionAuthenticationAdapterSettings
        )

    def test_settings_without_configure(self):
        adapter = CookieSessionAuthenticationAdapter()
        with pytest.raises(
            RuntimeError,
            match="The settings should never be accessed before the adapter was configured!",
        ):
            _ = adapter.settings

    def test_get_client_without_configure(self):
        adapter = CookieSessionAuthenticationAdapter()
        with pytest.raises(
            RuntimeError,
            match="The OAuth client should never be accessed before the adapter was configured!",
        ):
            adapter._get_client()

    @pytest.mark.asyncio
    async def test_configure_registers_oidc_client(
        self, settings: CookieSessionAuthenticationAdapterSettings
    ):
        adapter = CookieSessionAuthenticationAdapter()
        await adapter.configure(settings)
        assert adapter._settings == settings
        assert adapter._oauth is not None
        client = adapter._get_client()
        assert client is not None
        assert client.client_kwargs["timeout"] == settings.request_timeout
        # Confidential client: without this the token and refresh calls are rejected.
        assert client.client_secret == settings.client_secret

    @pytest.mark.asyncio
    async def test_configure_rebuilds_the_codec_for_the_new_secret(
        self, settings: CookieSessionAuthenticationAdapterSettings
    ):
        adapter = CookieSessionAuthenticationAdapter()
        adapter._settings = settings
        first = adapter._cookie_codec
        await adapter.configure(replace(settings, cookie_secret="other"))
        assert adapter._cookie_codec is not first

    # --- helpers ------------------------------------------------------------------

    def test_token_expiry_from_expires_at(self, adapter: CookieSessionAuthenticationAdapter):
        expires_at = 1_000_000_000
        result = adapter._token_expiry({"expires_at": expires_at})
        assert result == datetime.fromtimestamp(expires_at, tz=timezone.utc)

    def test_token_expiry_from_expires_in(self, adapter: CookieSessionAuthenticationAdapter):
        before = _now()
        result = adapter._token_expiry({"expires_in": 60})
        assert before + timedelta(seconds=59) <= result <= before + timedelta(seconds=61)

    def test_token_expiry_without_any_claim_uses_the_cookie_max_age(
        self, adapter: CookieSessionAuthenticationAdapter
    ):
        max_age = adapter.settings.cookie_max_age
        before = datetime.now(timezone.utc)
        result = adapter._token_expiry({})
        assert (
            before + timedelta(seconds=max_age - 1) <= result <= before + timedelta(seconds=max_age + 1)
        )

    @pytest.mark.parametrize(
        "candidate,expected",
        [
            ("/ui/users", "/ui/users"),
            ("//example.com", FRONTEND_PREFIX),
            ("https://example.com", FRONTEND_PREFIX),
            ("", FRONTEND_PREFIX),
        ],
    )
    def test_safe_next(self, adapter: CookieSessionAuthenticationAdapter, candidate: str, expected: str):
        assert adapter._safe_next(candidate) == expected

    def test_read_session_without_cookie(
        self, adapter: CookieSessionAuthenticationAdapter, mocker: MockerFixture
    ):
        request = self._request(mocker)
        assert adapter._read_session(request) is None
        assert self._pending(request) == "absent"

    def test_read_session_of_an_unreadable_cookie_asks_for_its_removal(
        self, adapter: CookieSessionAuthenticationAdapter, mocker: MockerFixture
    ):
        request = self._request(mocker, cookies={adapter.settings.cookie_name: "garbage"})
        assert adapter._read_session(request) is None
        assert self._pending(request) is None

    def test_read_session_valid(
        self, adapter: CookieSessionAuthenticationAdapter, mocker: MockerFixture
    ):
        record = _record()
        request = self._request(mocker, cookies=self._cookie(adapter, record))
        assert adapter._read_session(request) == record

    def test_read_session_past_the_absolute_deadline_asks_for_its_removal(
        self, adapter: CookieSessionAuthenticationAdapter, mocker: MockerFixture
    ):
        stale = _record(created_at=_now() - timedelta(seconds=adapter.settings.cookie_max_age + 60))
        request = self._request(mocker, cookies=self._cookie(adapter, stale))
        assert adapter._read_session(request) is None
        assert self._pending(request) is None

    def test_write_session_cookie_attributes(self, adapter: CookieSessionAuthenticationAdapter):
        response = Response()
        adapter._write_session(response, _record())
        morsel = _set_cookie_header(response)[adapter.settings.cookie_name]
        assert morsel["httponly"]
        assert morsel["secure"]
        assert morsel["samesite"] == "lax"
        assert morsel["path"] == SESSION_COOKIE_PATH

    def test_write_session_max_age_tracks_the_remaining_lifetime(
        self, adapter: CookieSessionAuthenticationAdapter
    ):
        half = adapter.settings.cookie_max_age // 2
        response = Response()
        adapter._write_session(response, _record(created_at=_now() - timedelta(seconds=half)))
        max_age = int(_set_cookie_header(response)[adapter.settings.cookie_name]["max-age"])
        assert half - 5 <= max_age <= half

    # --- login / callback ---------------------------------------------------------

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "next_url,expected",
        [("/ui/users", "/ui/users"), ("https://example.com", FRONTEND_PREFIX)],
        ids=["local", "discarded"],
    )
    async def test_login_redirect(
        self,
        wired: CookieSessionAuthenticationAdapter,
        client: MagicMock,
        mocker: MockerFixture,
        next_url: str,
        expected: str,
    ):
        sentinel = object()
        client.authorize_redirect = mocker.AsyncMock(return_value=sentinel)
        request = self._request(mocker, session={})
        result = await wired.login_redirect(request, next_url)
        assert result is sentinel
        assert request.session["post_login_next"] == expected
        client.authorize_redirect.assert_awaited_once_with(request, wired.settings.redirect_url)

    @pytest.mark.asyncio
    async def test_complete_login_puts_the_session_in_the_cookie(
        self,
        wired: CookieSessionAuthenticationAdapter,
        client: MagicMock,
        mocker: MockerFixture,
    ):
        client.authorize_access_token = mocker.AsyncMock(
            return_value={
                "userinfo": {
                    "preferred_username": "mina.teacher",
                    "name": "Mina Teacher",
                    "sub": "SUB",
                    "sid": "KCSID",
                },
                "expires_at": int(_future().timestamp()),
                "refresh_token": "RT",
                "id_token": "IDT",
            }
        )
        request = self._request(mocker, session={"post_login_next": "/ui/users"})
        response = await wired.complete_login(request)
        assert response.status_code == 303
        assert response.headers["location"] == "/ui/users"
        raw = _set_cookie_header(response)[wired.settings.cookie_name].value
        record = wired._cookie_codec.decode(raw)
        assert record is not None
        assert record.actor_id == "mina.teacher"
        assert record.display_name == "Mina Teacher"
        assert record.sub == "SUB"
        assert record.kc_sid == "KCSID"
        assert record.refresh_token == "RT"
        assert record.id_token == "IDT"
        assert record.csrf_token
        assert record.created_at <= _now()

    @pytest.mark.asyncio
    async def test_complete_login_without_the_display_name_claim_shows_the_actor_id(
        self,
        wired: CookieSessionAuthenticationAdapter,
        client: MagicMock,
        mocker: MockerFixture,
    ):
        client.authorize_access_token = mocker.AsyncMock(
            return_value={
                "userinfo": {"preferred_username": "mina.teacher", "sub": "SUB"},
                "expires_at": int(_future().timestamp()),
            }
        )
        response = await wired.complete_login(self._request(mocker))
        raw = _set_cookie_header(response)[wired.settings.cookie_name].value
        record = wired._cookie_codec.decode(raw)
        assert record is not None
        assert record.display_name == "mina.teacher"

    @pytest.mark.asyncio
    async def test_complete_login_oauth_error(
        self, wired: CookieSessionAuthenticationAdapter, client: MagicMock, mocker: MockerFixture
    ):
        client.authorize_access_token = mocker.AsyncMock(side_effect=OAuthError("bad state"))
        request = self._request(mocker, session={})
        with pytest.raises(NotAuthenticatedError, match="Not authenticated"):
            await wired.complete_login(request)

    @pytest.mark.asyncio
    async def test_complete_login_missing_identifier_claim(
        self, wired: CookieSessionAuthenticationAdapter, client: MagicMock, mocker: MockerFixture
    ):
        client.authorize_access_token = mocker.AsyncMock(
            return_value={"userinfo": {"sub": "SUB"}, "expires_in": 60}
        )
        request = self._request(mocker, session={})
        with pytest.raises(RuntimeError, match="does not contain the identifier claim"):
            await wired.complete_login(request)

    # --- logout -------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_logout_clears_the_cookie_and_redirects_to_end_session(
        self, wired: CookieSessionAuthenticationAdapter, client: MagicMock, mocker: MockerFixture
    ):
        client.load_server_metadata = mocker.AsyncMock(
            return_value={"end_session_endpoint": "https://kc/logout"}
        )
        request = self._request(mocker, cookies=self._cookie(wired, _record(id_token="THE_ID_TOKEN")))
        response = await wired.logout(request)
        assert response.status_code == 303
        location = response.headers["location"]
        assert location.startswith("https://kc/logout?")
        assert "id_token_hint=THE_ID_TOKEN" in location
        assert "post_logout_redirect_uri=" in location
        assert _cleared_paths(response, wired.settings.cookie_name) == {SESSION_COOKIE_PATH, "/"}

    @pytest.mark.asyncio
    async def test_logout_without_cookie(
        self, wired: CookieSessionAuthenticationAdapter, client: MagicMock, mocker: MockerFixture
    ):
        client.load_server_metadata = mocker.AsyncMock(
            return_value={"end_session_endpoint": "https://kc/logout"}
        )
        response = await wired.logout(self._request(mocker))
        assert response.status_code == 303
        assert "id_token_hint" not in response.headers["location"]

    @pytest.mark.asyncio
    async def test_logout_without_end_session_endpoint(
        self, wired: CookieSessionAuthenticationAdapter, client: MagicMock, mocker: MockerFixture
    ):
        client.load_server_metadata = mocker.AsyncMock(return_value={})
        request = self._request(mocker, cookies=self._cookie(wired, _record()))
        response = await wired.logout(request)
        assert response.headers["location"] == wired.settings.post_logout_redirect_url

    # --- authenticate / refresh ---------------------------------------------------

    @pytest.mark.asyncio
    async def test_authenticate_without_cookie(
        self, wired: CookieSessionAuthenticationAdapter, mocker: MockerFixture
    ):
        request = self._request(mocker)
        with pytest.raises(NotAuthenticatedError):
            await wired.get_authenticated_id(request)

    @pytest.mark.asyncio
    async def test_authenticate_with_an_unreadable_cookie(
        self, wired: CookieSessionAuthenticationAdapter, mocker: MockerFixture
    ):
        request = self._request(mocker, cookies={wired.settings.cookie_name: "garbage"})
        with pytest.raises(NotAuthenticatedError):
            await wired.get_authenticated_id(request)

    @pytest.mark.asyncio
    async def test_authenticate_valid(
        self, wired: CookieSessionAuthenticationAdapter, mocker: MockerFixture
    ):
        request = self._request(mocker, cookies=self._cookie(wired, _record()))
        assert await wired.get_authenticated_id(request) == "mina.teacher"
        assert self._pending(request) == "absent"

    @pytest.mark.asyncio
    async def test_authenticate_expired_refreshes_and_stashes_the_new_cookie(
        self, wired: CookieSessionAuthenticationAdapter, client: MagicMock, mocker: MockerFixture
    ):
        request = self._request(mocker, cookies=self._cookie(wired, _record(expires_at=_past())))
        _stub_refresh(mocker, client, {"expires_in": 3600, "refresh_token": "RT2", "id_token": "IDT2"})
        assert await wired.get_authenticated_id(request) == "mina.teacher"
        pending = self._pending(request)
        assert isinstance(pending, SessionRecord)
        assert pending.refresh_token == "RT2"
        assert pending.id_token == "IDT2"
        assert pending.expires_at > _now()
        client.fetch_access_token.assert_awaited_once_with(
            grant_type="refresh_token", refresh_token="rt"
        )

    @pytest.mark.asyncio
    async def test_authenticate_beyond_the_absolute_lifetime_refuses_to_refresh(
        self, wired: CookieSessionAuthenticationAdapter, client: MagicMock, mocker: MockerFixture
    ):
        stale = _record(
            created_at=_now() - timedelta(seconds=wired.settings.cookie_max_age + 60),
            expires_at=_past(),
        )
        client.fetch_access_token = mocker.AsyncMock(
            side_effect=AssertionError("Keycloak must not be asked to refresh an expired session")
        )
        request = self._request(mocker, cookies=self._cookie(wired, stale))
        with pytest.raises(NotAuthenticatedError):
            await wired.get_authenticated_id(request)
        assert self._pending(request) is None

    @pytest.mark.asyncio
    async def test_a_failed_refresh_asks_for_the_cookie_to_be_removed(
        self, wired: CookieSessionAuthenticationAdapter, client: MagicMock, mocker: MockerFixture
    ):
        request = self._request(mocker, cookies=self._cookie(wired, _record(expires_at=_past())))
        client.fetch_access_token = mocker.AsyncMock(
            side_effect=OAuthError(error="invalid_grant", description="Token is not active")
        )
        with pytest.raises(NotAuthenticatedError):
            await wired.get_authenticated_id(request)
        assert self._pending(request) is None

    @pytest.mark.asyncio
    async def test_refresh_without_refresh_token(self, wired: CookieSessionAuthenticationAdapter):
        record = _record(expires_at=_past(), refresh_token=None)
        with pytest.raises(NotAuthenticatedError):
            await wired._refresh(record)

    @pytest.mark.asyncio
    async def test_refresh_keeps_previous_tokens_when_absent(
        self, wired: CookieSessionAuthenticationAdapter, client: MagicMock, mocker: MockerFixture
    ):
        _stub_refresh(mocker, client, {"expires_in": 3600})
        updated = await wired._refresh(_record(expires_at=_past(), refresh_token="RT", id_token="IDT"))
        assert updated.refresh_token == "RT"
        assert updated.id_token == "IDT"
        assert updated.actor_id == "mina.teacher"
        client.parse_id_token.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_refresh_preserves_the_absolute_lifetime_anchor(
        self, wired: CookieSessionAuthenticationAdapter, client: MagicMock, mocker: MockerFixture
    ):
        original = _record(created_at=_now() - timedelta(hours=2), expires_at=_past())
        _stub_refresh(mocker, client, {"expires_in": 3600})
        assert (await wired._refresh(original)).created_at == original.created_at

    @pytest.mark.asyncio
    async def test_refresh_fails_on_a_transport_error(
        self, wired: CookieSessionAuthenticationAdapter, client: MagicMock, mocker: MockerFixture
    ):
        client.fetch_access_token = mocker.AsyncMock(side_effect=httpx.ConnectError("no route"))
        record = _record(expires_at=_past())
        with pytest.raises(NotAuthenticatedError):
            await wired._refresh(record)

    @pytest.mark.asyncio
    async def test_refresh_follows_a_renamed_actor(
        self, wired: CookieSessionAuthenticationAdapter, client: MagicMock, mocker: MockerFixture
    ):
        _stub_refresh(
            mocker,
            client,
            {"expires_in": 3600, "id_token": "IDT2"},
            {"sub": "sub-1", "preferred_username": "mina.married"},
        )
        updated = await wired._refresh(_record(expires_at=_past()))
        assert updated.actor_id == "mina.married"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "claims",
        [
            pytest.param(
                {"sub": "someone-else", "preferred_username": "mina.teacher"},
                id="a-changed-subject",
            ),
            pytest.param(ValueError("bad signature"), id="an-unverifiable-id-token"),
            pytest.param({"sub": "sub-1"}, id="no-identifier-claim"),
            pytest.param(
                {"sub": "sub-1", "preferred_username": ["mina.teacher"]},
                id="a-non-string-identifier-claim",
            ),
        ],
    )
    async def test_refresh_rejects_an_id_token_it_cannot_trust(
        self,
        wired: CookieSessionAuthenticationAdapter,
        client: MagicMock,
        mocker: MockerFixture,
        claims: dict[str, object] | Exception,
    ):
        """Every way the refreshed token can fail to prove it is still the same actor."""
        _stub_refresh(mocker, client, {"expires_in": 3600, "id_token": "IDT2"}, claims)
        record = _record(expires_at=_past())
        with pytest.raises(NotAuthenticatedError):
            await wired._refresh(record)

    # --- display name ---------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_get_display_name_from_the_session(
        self, wired: CookieSessionAuthenticationAdapter, mocker: MockerFixture
    ):
        request = self._request(mocker, cookies=self._cookie(wired, _record()))
        assert await wired.get_display_name(request) == "Mina Teacher"

    @pytest.mark.asyncio
    async def test_get_display_name_without_a_session(
        self, wired: CookieSessionAuthenticationAdapter, mocker: MockerFixture
    ):
        assert await wired.get_display_name(self._request(mocker)) == ""

    # --- handing the cookie to the response ---------------------------------------

    @pytest.mark.asyncio
    async def test_apply_pending_session_cookie_writes_the_refreshed_session(
        self, wired: CookieSessionAuthenticationAdapter, mocker: MockerFixture
    ):
        request = self._request(mocker)
        record = _record(refresh_token="RT2")
        wired._set_pending_session(request, record)
        response = Response()
        await wired.apply_pending_session_cookie(request, response)
        raw = _set_cookie_header(response)[wired.settings.cookie_name].value
        assert wired._cookie_codec.decode(raw) == record

    @pytest.mark.asyncio
    async def test_apply_pending_session_cookie_deletes_a_rejected_session(
        self, wired: CookieSessionAuthenticationAdapter, mocker: MockerFixture
    ):
        request = self._request(mocker)
        wired._set_pending_session(request, None)
        response = Response()
        await wired.apply_pending_session_cookie(request, response)
        assert _cleared_paths(response, wired.settings.cookie_name) == {SESSION_COOKIE_PATH, "/"}

    @pytest.mark.asyncio
    async def test_apply_pending_session_cookie_leaves_untouched_requests_alone(
        self, wired: CookieSessionAuthenticationAdapter, mocker: MockerFixture
    ):
        response = Response()
        await wired.apply_pending_session_cookie(self._request(mocker), response)
        assert "set-cookie" not in response.headers

    # --- port interface -----------------------------------------------------------

    @pytest.mark.asyncio
    async def test_get_authentication_dependency(
        self, adapter: CookieSessionAuthenticationAdapter, mocker: MockerFixture
    ):
        adapter.get_authenticated_id = mocker.AsyncMock(return_value="actor")
        dep = await adapter.get_authentication_dependency()
        assert await dep(self._request(mocker)) == "actor"

    @pytest.mark.asyncio
    async def test_a_cookie_minted_by_another_process_is_accepted(
        self,
        wired: CookieSessionAuthenticationAdapter,
        settings: CookieSessionAuthenticationAdapterSettings,
        mocker: MockerFixture,
    ):
        """Two instances stand in for two gunicorn workers, sharing only the secret."""
        other = CookieSessionAuthenticationAdapter()
        other._settings = settings
        response = Response()
        other._write_session(response, _record())
        raw = _set_cookie_header(response)[settings.cookie_name].value
        request = self._request(mocker, cookies={settings.cookie_name: raw})
        assert await wired.get_authenticated_id(request) == "mina.teacher"

    # --- CSRF ---------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_issue_csrf_token_returns_session_token(
        self, wired: CookieSessionAuthenticationAdapter, mocker: MockerFixture
    ):
        request = self._request(mocker, cookies=self._cookie(wired, _record(csrf_token="the-token")))
        assert await wired.issue_csrf_token(request) == "the-token"

    @pytest.mark.asyncio
    async def test_issue_csrf_token_without_cookie(
        self, wired: CookieSessionAuthenticationAdapter, mocker: MockerFixture
    ):
        assert await wired.issue_csrf_token(self._request(mocker)) == ""

    @pytest.mark.asyncio
    async def test_issue_csrf_token_with_an_unreadable_cookie(
        self, wired: CookieSessionAuthenticationAdapter, mocker: MockerFixture
    ):
        request = self._request(mocker, cookies={wired.settings.cookie_name: "garbage"})
        assert await wired.issue_csrf_token(request) == ""

    @pytest.mark.parametrize(
        "submitted,expected",
        [
            ("the-token", True),
            ("wrong", False),
            ("wröng", False),
            (None, False),
        ],
    )
    @pytest.mark.asyncio
    async def test_check_csrf_against_session(
        self,
        wired: CookieSessionAuthenticationAdapter,
        mocker: MockerFixture,
        submitted: str | None,
        expected: bool,
    ):
        request = self._request(mocker, cookies=self._cookie(wired, _record(csrf_token="the-token")))
        assert await wired.check_csrf(request, submitted) is expected

    @pytest.mark.asyncio
    async def test_check_csrf_without_session_is_rejected(
        self, wired: CookieSessionAuthenticationAdapter, mocker: MockerFixture
    ):
        assert await wired.check_csrf(self._request(mocker), "anything") is False


class TestAlwaysAuthenticatedAdapter:
    @pytest.fixture
    def adapter(self) -> AlwaysAuthenticatedAdapter:
        return AlwaysAuthenticatedAdapter()

    @pytest.mark.asyncio
    async def test_get_authentication_dependency(self, adapter: AlwaysAuthenticatedAdapter):
        assert await (await adapter.get_authentication_dependency())() == "dev"

    @pytest.mark.asyncio
    async def test_get_authenticated_id(
        self, adapter: AlwaysAuthenticatedAdapter, mocker: MockerFixture
    ):
        assert await adapter.get_authenticated_id(mocker.Mock())

    @pytest.mark.asyncio
    async def test_default_login_redirect_ignores_next(
        self, adapter: AlwaysAuthenticatedAdapter, mocker: MockerFixture
    ):
        response = await adapter.login_redirect(mocker.Mock(), "/ui/users")
        assert response.status_code == 303
        assert response.headers["location"] == FRONTEND_PREFIX

    @pytest.mark.asyncio
    async def test_default_login_redirect_without_next(
        self, adapter: AlwaysAuthenticatedAdapter, mocker: MockerFixture
    ):
        response = await adapter.login_redirect(mocker.Mock())
        assert response.headers["location"] == FRONTEND_PREFIX

    @pytest.mark.asyncio
    async def test_default_complete_login(
        self, adapter: AlwaysAuthenticatedAdapter, mocker: MockerFixture
    ):
        response = await adapter.complete_login(mocker.Mock())
        assert response.status_code == 303
        assert response.headers["location"] == FRONTEND_PREFIX

    @pytest.mark.asyncio
    async def test_default_logout(self, adapter: AlwaysAuthenticatedAdapter, mocker: MockerFixture):
        response = await adapter.logout(mocker.Mock())
        assert response.status_code == 303
        assert response.headers["location"] == FRONTEND_PREFIX

    @pytest.mark.asyncio
    async def test_issue_csrf_token_is_empty(
        self, adapter: AlwaysAuthenticatedAdapter, mocker: MockerFixture
    ):
        assert await adapter.issue_csrf_token(mocker.Mock()) == ""

    @pytest.mark.asyncio
    async def test_check_csrf_accepts_anything(
        self, adapter: AlwaysAuthenticatedAdapter, mocker: MockerFixture
    ):
        assert await adapter.check_csrf(mocker.Mock(), None) is True
        assert await adapter.check_csrf(mocker.Mock(), "anything") is True

    @pytest.mark.asyncio
    async def test_apply_pending_session_cookie_is_a_no_op(
        self, adapter: AlwaysAuthenticatedAdapter, mocker: MockerFixture
    ):
        response = Response()
        await adapter.apply_pending_session_cookie(mocker.Mock(), response)
        assert "set-cookie" not in response.headers

    def test_get_settings_cls(self, adapter: AlwaysAuthenticatedAdapter):
        assert adapter.get_settings_cls() is AlwaysAuthenticatedAdapterSettings

    @pytest.mark.asyncio
    async def test_configure_overrides_the_default_actor(
        self, adapter: AlwaysAuthenticatedAdapter, mocker: MockerFixture
    ):
        await adapter.configure(AlwaysAuthenticatedAdapterSettings(actor_id="demo_teacher"))
        assert await adapter.get_authenticated_id(mocker.Mock()) == "demo_teacher"
        assert await (await adapter.get_authentication_dependency())() == "demo_teacher"


class TestNeverAuthenticatedAdapter:
    @pytest.fixture
    def adapter(self) -> NeverAuthenticatedAdapter:
        return NeverAuthenticatedAdapter()

    @pytest.mark.asyncio
    async def test_get_authentication_dependency(self, adapter: NeverAuthenticatedAdapter):
        dependency = await adapter.get_authentication_dependency()
        with pytest.raises(NotAuthenticatedError, match="Never authenticated."):
            await dependency()

    @pytest.mark.asyncio
    async def test_get_authenticated_id(self, adapter: NeverAuthenticatedAdapter, mocker: MockerFixture):
        request = mocker.Mock()
        with pytest.raises(NotAuthenticatedError, match="Never authenticated."):
            await adapter.get_authenticated_id(request)
