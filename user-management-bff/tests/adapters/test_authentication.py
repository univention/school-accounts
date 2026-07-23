# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
from datetime import datetime, timedelta, timezone

import pytest
from authlib.integrations.starlette_client import OAuthError

import user_management_bff.adapters.authentication as authentication
from user_management_bff.adapters.authentication import (
    AlwaysAuthenticatedAdapter,
    CookieSessionAuthenticationAdapter,
    CookieSessionAuthenticationAdapterSettings,
    NeverAuthenticatedAdapter,
)
from user_management_bff.adapters.session_store import InMemorySessionStoreAdapter
from user_management_bff.constants import FRONTEND_PREFIX
from user_management_bff.errors import NotAuthenticatedError
from user_management_bff.models import SessionRecord


def _future() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=1)


def _past() -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=1)


def _record(**overrides) -> SessionRecord:
    data = {
        "actor_id": "mina.teacher",
        "sub": "sub-1",
        "kc_sid": "kc-1",
        "expires_at": _future(),
        "refresh_token": "rt",
        "id_token": "idt",
    }
    data.update(overrides)
    return SessionRecord(**data)


class FakeAsyncClient:
    """Minimal async-context httpx.AsyncClient stand-in for refresh tests."""

    def __init__(self, response):
        self._response = response
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, data=None, timeout=None):
        self.calls.append((url, data, timeout))
        return self._response


def _patch_httpx(mocker, response):
    mocker.patch.object(authentication.httpx, "AsyncClient", lambda *a, **k: FakeAsyncClient(response))


class TestCookieSessionAuthenticationAdapter:
    @pytest.fixture
    def settings(self) -> CookieSessionAuthenticationAdapterSettings:
        return CookieSessionAuthenticationAdapterSettings(
            well_known_url="https://kc/realms/ucs/.well-known/openid-configuration",
            client_id="ucsschool-user-management-ui",
            redirect_url="https://app/ui/auth/callback",
            cookie_secret="unit-test-secret",
            post_logout_redirect_url="https://app/ui",
        )

    @pytest.fixture
    def adapter(self, settings) -> CookieSessionAuthenticationAdapter:
        adapter = CookieSessionAuthenticationAdapter()
        adapter._settings = settings
        return adapter

    @pytest.fixture
    def store(self) -> InMemorySessionStoreAdapter:
        return InMemorySessionStoreAdapter()

    @pytest.fixture
    def client(self, mocker):
        return mocker.MagicMock()

    @pytest.fixture
    def wired(self, adapter, store, client, mocker):
        adapter._get_client = lambda: client
        adapter._session_store = mocker.AsyncMock(return_value=store)
        return adapter

    def _request(self, mocker, *, cookies=None, session=None):
        request = mocker.MagicMock()
        request.cookies = cookies if cookies is not None else {}
        request.session = session if session is not None else {}
        return request

    def _signed_cookie(self, adapter, session_id):
        return {adapter.settings.cookie_name: adapter._serializer.dumps(session_id)}

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

    @pytest.mark.asyncio
    async def test_configure_registers_oidc_client(self, settings):
        adapter = CookieSessionAuthenticationAdapter()
        await adapter.configure(settings)
        assert adapter._settings == settings
        assert adapter._oauth is not None
        assert adapter._get_client() is not None

    # --- helpers ------------------------------------------------------------------

    def test_token_expiry_from_expires_at(self, adapter):
        expires_at = 1_000_000_000
        result = adapter._token_expiry({"expires_at": expires_at})
        assert result == datetime.fromtimestamp(expires_at, tz=timezone.utc)

    def test_token_expiry_from_expires_in(self, adapter):
        before = datetime.now(timezone.utc)
        result = adapter._token_expiry({"expires_in": 60})
        assert before + timedelta(seconds=59) <= result <= before + timedelta(seconds=61)

    @pytest.mark.parametrize(
        "candidate,expected",
        [
            ("/ui/users", "/ui/users"),
            ("//evil.com", FRONTEND_PREFIX),
            ("https://evil.com", FRONTEND_PREFIX),
            ("", FRONTEND_PREFIX),
        ],
    )
    def test_safe_next(self, adapter, candidate, expected):
        assert adapter._safe_next(candidate) == expected

    def test_read_cookie_missing(self, adapter, mocker):
        assert adapter._read_cookie(self._request(mocker)) is None

    def test_read_cookie_bad_signature(self, adapter, mocker):
        request = self._request(mocker, cookies={adapter.settings.cookie_name: "garbage"})
        assert adapter._read_cookie(request) is None

    def test_read_cookie_valid(self, adapter, mocker):
        request = self._request(mocker, cookies=self._signed_cookie(adapter, "sid-1"))
        assert adapter._read_cookie(request) == "sid-1"

    # --- login / callback ---------------------------------------------------------

    @pytest.mark.asyncio
    async def test_login_redirect(self, wired, client, mocker):
        sentinel = object()
        client.authorize_redirect = mocker.AsyncMock(return_value=sentinel)
        request = self._request(mocker, session={})
        result = await wired.login_redirect(request, "/ui/users")
        assert result is sentinel
        assert request.session["post_login_next"] == "/ui/users"
        client.authorize_redirect.assert_awaited_once_with(request, wired.settings.redirect_url)

    @pytest.mark.asyncio
    async def test_complete_login_creates_session(self, wired, store, client, mocker):
        client.authorize_access_token = mocker.AsyncMock(
            return_value={
                "userinfo": {"preferred_username": "mina.teacher", "sub": "SUB", "sid": "KCSID"},
                "expires_at": int(_future().timestamp()),
                "refresh_token": "RT",
                "id_token": "IDT",
            }
        )
        request = self._request(mocker, session={"post_login_next": "/ui/users"})
        response = await wired.complete_login(request)
        assert response.status_code == 303
        assert response.headers["location"] == "/ui/users"
        assert wired.settings.cookie_name in response.headers["set-cookie"]
        assert len(store._store) == 1
        record = next(iter(store._store.values()))
        assert record.actor_id == "mina.teacher"
        assert record.sub == "SUB"
        assert record.kc_sid == "KCSID"

    @pytest.mark.asyncio
    async def test_complete_login_oauth_error(self, wired, client, mocker):
        client.authorize_access_token = mocker.AsyncMock(side_effect=OAuthError("bad state"))
        with pytest.raises(NotAuthenticatedError, match="Not authenticated"):
            await wired.complete_login(self._request(mocker, session={}))

    @pytest.mark.asyncio
    async def test_complete_login_missing_identifier_claim(self, wired, client, mocker):
        client.authorize_access_token = mocker.AsyncMock(
            return_value={"userinfo": {"sub": "SUB"}, "expires_in": 60}
        )
        with pytest.raises(RuntimeError, match="does not contain the identifier claim"):
            await wired.complete_login(self._request(mocker, session={}))

    # --- logout -------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_logout_clears_session_and_redirects_to_end_session(
        self, wired, store, client, mocker
    ):
        session_id = await store.create(_record(id_token="THE_ID_TOKEN"))
        client.load_server_metadata = mocker.AsyncMock(
            return_value={"end_session_endpoint": "https://kc/logout"}
        )
        request = self._request(mocker, cookies=self._signed_cookie(wired, session_id))
        response = await wired.logout(request)
        assert response.status_code == 303
        location = response.headers["location"]
        assert location.startswith("https://kc/logout?")
        assert "id_token_hint=THE_ID_TOKEN" in location
        assert "post_logout_redirect_uri=" in location
        assert await store.get(session_id) is None
        assert wired.settings.cookie_name in response.headers["set-cookie"]

    @pytest.mark.asyncio
    async def test_logout_without_cookie(self, wired, client, mocker):
        client.load_server_metadata = mocker.AsyncMock(
            return_value={"end_session_endpoint": "https://kc/logout"}
        )
        response = await wired.logout(self._request(mocker))
        assert response.status_code == 303
        assert "id_token_hint" not in response.headers["location"]

    @pytest.mark.asyncio
    async def test_logout_without_end_session_endpoint(self, wired, store, client, mocker):
        session_id = await store.create(_record())
        client.load_server_metadata = mocker.AsyncMock(return_value={})
        request = self._request(mocker, cookies=self._signed_cookie(wired, session_id))
        response = await wired.logout(request)
        assert response.headers["location"] == wired.settings.post_logout_redirect_url

    # --- refresh / authenticate ---------------------------------------------------

    @pytest.mark.asyncio
    async def test_authenticate_missing_cookie(self, wired, store, mocker):
        with pytest.raises(NotAuthenticatedError):
            await wired._authenticate(self._request(mocker), store)

    @pytest.mark.asyncio
    async def test_authenticate_unknown_session(self, wired, store, mocker):
        request = self._request(mocker, cookies=self._signed_cookie(wired, "ghost"))
        with pytest.raises(NotAuthenticatedError):
            await wired._authenticate(request, store)

    @pytest.mark.asyncio
    async def test_authenticate_valid(self, wired, store, mocker):
        session_id = await store.create(_record())
        request = self._request(mocker, cookies=self._signed_cookie(wired, session_id))
        assert await wired._authenticate(request, store) == "mina.teacher"

    @pytest.mark.asyncio
    async def test_authenticate_expired_triggers_refresh(self, wired, store, client, mocker):
        session_id = await store.create(_record(expires_at=_past(), refresh_token="RT"))
        client.load_server_metadata = mocker.AsyncMock(
            return_value={"token_endpoint": "https://kc/token"}
        )
        response = mocker.MagicMock()
        response.status_code = 200
        response.json.return_value = {"expires_in": 3600, "refresh_token": "RT2", "id_token": "IDT2"}
        _patch_httpx(mocker, response)
        request = self._request(mocker, cookies=self._signed_cookie(wired, session_id))
        assert await wired._authenticate(request, store) == "mina.teacher"
        refreshed = await store.get(session_id)
        assert refreshed.refresh_token == "RT2"
        assert refreshed.id_token == "IDT2"
        assert refreshed.expires_at > datetime.now(timezone.utc)

    @pytest.mark.asyncio
    async def test_refresh_without_refresh_token(self, wired, store, mocker):
        session_id = await store.create(_record(expires_at=_past(), refresh_token=None))
        with pytest.raises(NotAuthenticatedError):
            await wired._refresh(session_id, await store.get(session_id), store)
        assert await store.get(session_id) is None

    @pytest.mark.asyncio
    async def test_refresh_http_error_requires_relogin(self, wired, store, client, mocker):
        session_id = await store.create(_record(expires_at=_past(), refresh_token="RT"))
        client.load_server_metadata = mocker.AsyncMock(
            return_value={"token_endpoint": "https://kc/token"}
        )
        response = mocker.MagicMock()
        response.status_code = 400
        _patch_httpx(mocker, response)
        with pytest.raises(NotAuthenticatedError):
            await wired._refresh(session_id, await store.get(session_id), store)
        assert await store.get(session_id) is None

    @pytest.mark.asyncio
    async def test_refresh_keeps_previous_tokens_when_absent(self, wired, store, client, mocker):
        session_id = await store.create(_record(expires_at=_past(), refresh_token="RT", id_token="IDT"))
        client.load_server_metadata = mocker.AsyncMock(
            return_value={"token_endpoint": "https://kc/token"}
        )
        response = mocker.MagicMock()
        response.status_code = 200
        response.json.return_value = {"expires_in": 3600}
        _patch_httpx(mocker, response)
        updated = await wired._refresh(session_id, await store.get(session_id), store)
        assert updated.refresh_token == "RT"
        assert updated.id_token == "IDT"

    # --- port interface -----------------------------------------------------------

    @pytest.mark.asyncio
    async def test_get_authenticated_id_resolves_store_from_registry(self, adapter, store, mocker):
        session_id = await store.create(_record())
        mocker.patch.object(authentication, "ADAPTER_REGISTRY", mocker.AsyncMock(return_value=store))
        request = self._request(mocker, cookies=self._signed_cookie(adapter, session_id))
        assert await adapter.get_authenticated_id(request) == "mina.teacher"

    @pytest.mark.asyncio
    async def test_get_authentication_dependency(self, adapter, mocker):
        adapter.get_authenticated_id = mocker.AsyncMock(return_value="actor")
        dep = await adapter.get_authentication_dependency()
        assert await dep(self._request(mocker)) == "actor"


class TestAlwaysAuthenticatedAdapter:
    @pytest.fixture
    def adapter(self) -> AlwaysAuthenticatedAdapter:
        return AlwaysAuthenticatedAdapter()

    @pytest.mark.asyncio
    async def test_get_authentication_dependency(self, adapter):
        assert await (await adapter.get_authentication_dependency())() == "dev"

    @pytest.mark.asyncio
    async def test_get_authenticated_id(self, adapter, mocker):
        assert await adapter.get_authenticated_id(mocker.Mock())

    @pytest.mark.asyncio
    async def test_default_login_redirect_with_next(self, adapter, mocker):
        response = await adapter.login_redirect(mocker.Mock(), "/ui/users")
        assert response.status_code == 303
        assert response.headers["location"] == "/ui/users"

    @pytest.mark.asyncio
    async def test_default_login_redirect_without_next(self, adapter, mocker):
        response = await adapter.login_redirect(mocker.Mock())
        assert response.headers["location"] == FRONTEND_PREFIX

    @pytest.mark.asyncio
    async def test_default_complete_login(self, adapter, mocker):
        response = await adapter.complete_login(mocker.Mock())
        assert response.status_code == 303
        assert response.headers["location"] == FRONTEND_PREFIX

    @pytest.mark.asyncio
    async def test_default_logout(self, adapter, mocker):
        response = await adapter.logout(mocker.Mock())
        assert response.status_code == 303
        assert response.headers["location"] == FRONTEND_PREFIX


class TestNeverAuthenticatedAdapter:
    @pytest.fixture
    def adapter(self) -> NeverAuthenticatedAdapter:
        return NeverAuthenticatedAdapter()

    @pytest.mark.asyncio
    async def test_get_authentication_dependency(self, adapter):
        with pytest.raises(NotAuthenticatedError, match="Never authenticated."):
            await (await adapter.get_authentication_dependency())()

    @pytest.mark.asyncio
    async def test_get_authenticated_id(self, adapter, mocker):
        with pytest.raises(NotAuthenticatedError, match="Never authenticated."):
            await adapter.get_authenticated_id(mocker.Mock())
