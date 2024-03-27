# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import time
from typing import Callable

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from httpx import RequestError

import user_management_bff
from user_management_bff.adapters.authentication import (
    AlwaysAuthenticatedAdapter,
    NeverAuthenticatedAdapter,
    Oauth2FastAPIAuthenticationAdapter,
    Oauth2FastAPIAuthenticationAdapterSettings,
)
from user_management_bff.errors import NotAuthenticatedError


class TestOauth2FastAPIAuthenticationAdapter:
    @pytest.fixture
    def adapter(self):
        return Oauth2FastAPIAuthenticationAdapter()

    @pytest.fixture
    def settings(self):
        return Oauth2FastAPIAuthenticationAdapterSettings(
            well_known_url="https://example.com",
            audience="ucsschool-user-management",
            identifier_claim="dn",
        )

    @pytest.fixture
    def configured_adapter(self, adapter, settings):
        adapter._settings = settings
        return adapter

    @pytest.fixture
    def mocked_adapter(self, configured_adapter, mocker):
        get_oauth2_settings_mock = mocker.AsyncMock().get
        get_oauth2_settings_mock.return_value = {
            "authorization_endpoint": "https://authorization.example.com",
            "token_endpoint": "https://token.example.com",
            "issuer": "ISSUER",
            "jwks_uri": "https://jwks.example.com",
        }
        configured_adapter._get_oauth2_settings = get_oauth2_settings_mock
        return configured_adapter

    @pytest.fixture
    def gen_rsa_key(self) -> Callable[[], RSAPrivateKey]:
        def _gen_rsa_key() -> RSAPrivateKey:
            return rsa.generate_private_key(public_exponent=65537, key_size=2048)

        return _gen_rsa_key

    @pytest.fixture
    def mock_pyjwt_client(self, mocker, monkeypatch):
        def _mock_pyjwt_client(private_key):
            key_mock = mocker.MagicMock()
            key_mock.key = private_key.public_key()
            pyjwt_client_instance_mock = mocker.MagicMock()
            pyjwt_client_instance_mock.get_signing_key_from_jwt.return_value = key_mock
            pyjwt_mock = mocker.MagicMock(return_value=pyjwt_client_instance_mock)
            monkeypatch.setattr(user_management_bff.adapters.authentication, "PyJWKClient", pyjwt_mock)

        return _mock_pyjwt_client

    def test_get_settings_cls(self):
        assert (
            Oauth2FastAPIAuthenticationAdapter.get_settings_cls()
            == Oauth2FastAPIAuthenticationAdapterSettings
        )

    def test_settings_without_configure(self, adapter):
        with pytest.raises(
            RuntimeError,
            match="The settings should never be accessed before the adapter was configured!",
        ):
            _settings = adapter.settings

    @pytest.mark.asyncio
    async def test__get_oauth2_settings(self, configured_adapter, monkeypatch, mocker, settings):
        response_mock = mocker.MagicMock()
        response_mock.status_code = 200
        response_mock.json.return_value = {"foo": "bar"}

        async def get_mock(self, *args, **kwargs):
            assert args == (settings.well_known_url,)
            assert kwargs == {"timeout": settings.request_timeout}
            return response_mock

        monkeypatch.setattr(user_management_bff.utils.AsyncClient, "get", get_mock)
        assert await configured_adapter._get_oauth2_settings() == {"foo": "bar"}

    @pytest.mark.asyncio
    async def test__get_oauth2_settings_wrong_status_code(
        self, configured_adapter, monkeypatch, mocker, settings
    ):
        response_mock = mocker.MagicMock()
        response_mock.status_code = 404

        async def get_mock(*args, **kwargs):
            return response_mock

        monkeypatch.setattr(user_management_bff.utils.AsyncClient, "get", get_mock)
        with pytest.raises(
            RuntimeError, match="^Could not load oauth2 settings from https://example.com: '"
        ):
            await configured_adapter._get_oauth2_settings()

    @pytest.mark.asyncio
    async def test__get_oauth2_settings_exc(self, configured_adapter, monkeypatch, settings):
        async def get_mock(*args, **kwargs):
            raise RequestError("ERROR MESSAGE")

        monkeypatch.setattr(user_management_bff.utils.AsyncClient, "get", get_mock)
        with pytest.raises(
            RuntimeError,
            match="Could not load oauth2 settings from https://example.com: 'ERROR MESSAGE'",
        ):
            await configured_adapter._get_oauth2_settings()

    @pytest.mark.asyncio
    async def test_configure(self, adapter, settings):
        await adapter.configure(settings)
        assert adapter._settings == settings

    @pytest.mark.asyncio
    async def test_get_authentication_dependency_valid_token(
        self, mocked_adapter, monkeypatch, gen_rsa_key, mock_pyjwt_client
    ):
        private_key = gen_rsa_key()
        mock_pyjwt_client(private_key)
        dep = await mocked_adapter.get_authentication_dependency()
        payload = {
            "iss": "ISSUER",
            "aud": ["ucsschool-user-management-ui", "ucsschool-user-management", "account"],
            "sub": "admin",
            "dn": "DN",
            "iat": time.time(),
            "exp": time.time() + 500,
            "jti": "9f2cd5fe-9e15-409a-967a-7f2c3f640621",
        }
        token = jwt.encode(payload, private_key, algorithm="RS256")
        assert await dep(token=token) == "DN"

    @pytest.mark.asyncio
    async def test_get_authentication_dependency_missing_identifier(
        self, mocked_adapter, monkeypatch, gen_rsa_key, mock_pyjwt_client
    ):
        private_key = gen_rsa_key()
        mock_pyjwt_client(private_key)
        dep = await mocked_adapter.get_authentication_dependency()
        payload = {
            "iss": "ISSUER",
            "aud": ["ucsschool-user-management-ui", "ucsschool-user-management", "account"],
            "sub": "admin",
            "iat": time.time(),
            "exp": time.time() + 500,
            "jti": "9f2cd5fe-9e15-409a-967a-7f2c3f640621",
        }
        token = jwt.encode(payload, private_key, algorithm="RS256")
        with pytest.raises(
            RuntimeError,
            match="The token does not contain the identifier claim dn. "
            "Please check the settings of the oauth provider.",
        ):
            await dep(token=token)

    @pytest.mark.parametrize(
        "overrides",
        [
            {"iss": "OTHER"},
            {"aud": ["OTHER", "OTHER2"]},
            {"iat": time.time() + 1000, "exp": time.time() + 1500},
            {"iat": time.time() - 1000, "exp": time.time() - 500},
        ],
    )
    @pytest.mark.asyncio
    async def test_get_authentication_dependency_invalid_token(
        self, mocked_adapter, monkeypatch, gen_rsa_key, mock_pyjwt_client, overrides
    ):
        private_key = gen_rsa_key()
        mock_pyjwt_client(private_key)
        dep = await mocked_adapter.get_authentication_dependency()
        payload = {
            "iss": "ISSUER",
            "aud": ["ucsschool-user-management-ui", "ucsschool-user-management", "account"],
            "sub": "admin",
            "iat": time.time(),
            "exp": time.time() + 500,
            "jti": "9f2cd5fe-9e15-409a-967a-7f2c3f640621",
        }
        payload.update(overrides)
        token = jwt.encode(payload, private_key, algorithm="RS256")
        with pytest.raises(NotAuthenticatedError, match="Not authenticated"):
            await dep(token=token)

    @pytest.mark.asyncio
    async def test_get_authentication_dependency_wrong_key(
        self, mocked_adapter, monkeypatch, gen_rsa_key, mock_pyjwt_client
    ):
        private_key = gen_rsa_key()
        private_key2 = gen_rsa_key()
        mock_pyjwt_client(private_key)
        dep = await mocked_adapter.get_authentication_dependency()
        payload = {
            "iss": "ISSUER",
            "aud": ["ucsschool-user-management-ui", "ucsschool-user-management", "account"],
            "sub": "admin",
            "iat": time.time(),
            "exp": time.time() + 500,
            "jti": "9f2cd5fe-9e15-409a-967a-7f2c3f640621",
        }
        token = jwt.encode(payload, private_key2, algorithm="RS256")
        with pytest.raises(NotAuthenticatedError, match="Not authenticated"):
            await dep(token=token)

    @pytest.mark.asyncio
    async def test_get_authenticated_id(self, mocked_adapter, gen_rsa_key, mock_pyjwt_client, mocker):
        request_mock = mocker.MagicMock()
        private_key = gen_rsa_key()
        mock_pyjwt_client(private_key)
        payload = {
            "iss": "ISSUER",
            "aud": ["ucsschool-user-management-ui", "ucsschool-user-management", "account"],
            "sub": "admin",
            "dn": "DN",
            "iat": time.time(),
            "exp": time.time() + 500,
            "jti": "9f2cd5fe-9e15-409a-967a-7f2c3f640621",
        }
        token = jwt.encode(payload, private_key, algorithm="RS256")

        async def _return_token(*args, **kwargs):
            return token

        get_oauth2_scheme_mock = mocker.MagicMock(return_value=mocker.Mock(return_value=_return_token()))
        mocked_adapter._get_oauth2_scheme = get_oauth2_scheme_mock
        assert await mocked_adapter.get_authenticated_id(request_mock) == "DN"


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
