# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import pytest
from httpx import RequestError

import user_management_bff
from user_management_bff.utils import get_oauth2_settings


@pytest.mark.asyncio
async def test_get_oauth2_settings(monkeypatch, mocker):
    response_mock = mocker.MagicMock()
    response_mock.status_code = 200
    response_mock.json.return_value = {"foo": "bar"}

    async def get_mock(*args, **kwargs):
        return response_mock

    monkeypatch.setattr(user_management_bff.utils.AsyncClient, "get", get_mock)
    assert await get_oauth2_settings("URL", 10) == {"foo": "bar"}


@pytest.mark.asyncio
async def test_get_oauth2_settings_wrong_status_code(monkeypatch, mocker):
    response_mock = mocker.MagicMock()
    response_mock.status_code = 404

    async def get_mock(*args, **kwargs):
        return response_mock

    monkeypatch.setattr(user_management_bff.utils.AsyncClient, "get", get_mock)
    with pytest.raises(
        RuntimeError, match="^Could not load oauth2 settings from https://example.com: '"
    ):
        await get_oauth2_settings("https://example.com", 10)


@pytest.mark.asyncio
async def test_get_oauth2_settings_exc(monkeypatch):
    async def get_mock(*args, **kwargs):
        raise RequestError("ERROR MESSAGE")

    monkeypatch.setattr(user_management_bff.utils.AsyncClient, "get", get_mock)
    with pytest.raises(
        RuntimeError,
        match="Could not load oauth2 settings from https://example.com: 'ERROR MESSAGE'",
    ):
        await get_oauth2_settings("https://example.com", 10)
