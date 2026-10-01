# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""The session must not belong to the process that issued it.

Every other test in the suite runs in one process, so none of them can tell a
stateless session apart from a process-local one. These start real gunicorn
servers instead.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import httpx
import pytest

from ucsschool_accounts.constants import FRONTEND_PREFIX
from ucsschool_accounts.models import SessionRecord
from ucsschool_accounts.session_cookie import SessionCookieCodec

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path
    from typing import TextIO

COOKIE_SECRET = "b4c8f0e2a6d1937584bf0c2e6a1d9358b4c8f0e2a6d1937584bf0c2e6a1d9358"
COOKIE_NAME = "ucsschool_accounts_session"
SHELL_PATH = f"{FRONTEND_PREFIX}/"
BOOT_TIMEOUT = 60.0


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _server_env() -> dict[str, str]:
    # The well-known URL is deliberately unreachable: a live session never asks
    # Keycloak anything, so a request that tried to fails loudly instead of
    # passing for the wrong reason.
    env = dict(os.environ)
    env.update(
        {
            "UCSSCHOOL_ACCOUNTS__ADAPTER__AUTHENTICATION": (
                "ucsschool_accounts.adapters.authentication:CookieSessionAuthenticationAdapter"
            ),
            "COOKIE_SESSION_AUTHENTICATION_ADAPTER__WELL_KNOWN_URL": (
                "http://127.0.0.1:1/realms/ucs/.well-known/openid-configuration"
            ),
            "COOKIE_SESSION_AUTHENTICATION_ADAPTER__CLIENT_ID": "ucsschool-accounts-ui",
            "COOKIE_SESSION_AUTHENTICATION_ADAPTER__REDIRECT_URL": (
                f"http://127.0.0.1{FRONTEND_PREFIX}/auth/callback"
            ),
            "COOKIE_SESSION_AUTHENTICATION_ADAPTER__COOKIE_SECRET": COOKIE_SECRET,
            "COOKIE_SESSION_AUTHENTICATION_ADAPTER__COOKIE_NAME": COOKIE_NAME,
            "COOKIE_SESSION_AUTHENTICATION_ADAPTER__COOKIE_SECURE": "false",
            "UCSSCHOOL_ACCOUNTS__SESSION_SECRET": COOKIE_SECRET,
            "UCSSCHOOL_ACCOUNTS__SESSION_COOKIE_SECURE": "false",
        }
    )
    return env


class _Server:
    def __init__(self, workers: int, log_path: Path) -> None:
        self.port: int = _free_port()
        self._log: TextIO = log_path.open("w+", encoding="utf-8")
        self._process: subprocess.Popen[bytes] = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "gunicorn",
                "--worker-class",
                "uvicorn.workers.UvicornWorker",
                "--workers",
                str(workers),
                "--bind",
                f"127.0.0.1:{self.port}",
                "--log-level",
                "info",
                "--graceful-timeout",
                "2",
                "ucsschool_accounts.main:app",
            ],
            env=_server_env(),
            stdout=self._log,
            stderr=subprocess.STDOUT,
        )

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}{SHELL_PATH}"

    def get(self, cookies: dict[str, str] | None = None) -> httpx.Response:
        return httpx.get(self.url, cookies=cookies or {}, follow_redirects=False, timeout=10.0)

    def wait_until_serving(self) -> None:
        deadline = time.monotonic() + BOOT_TIMEOUT
        while time.monotonic() < deadline:
            if self._process.poll() is not None:
                pytest.fail(f"gunicorn exited early:\n{self.log()}")
            try:
                if self.get().status_code == 303:
                    return
            except httpx.HTTPError:
                time.sleep(0.2)
        pytest.fail(f"gunicorn did not start within {BOOT_TIMEOUT}s:\n{self.log()}")

    def booted_workers(self) -> int:
        return self.log().count("Booting worker with pid")

    def log(self) -> str:
        self._log.flush()
        self._log.seek(0)
        return self._log.read()

    def stop(self) -> None:
        self._process.terminate()
        try:
            self._process.wait(timeout=15)
        except subprocess.TimeoutExpired:  # pragma: no cover
            self._process.kill()
            self._process.wait(timeout=15)
        self._log.close()


@pytest.fixture(scope="module")
def session_cookie() -> dict[str, str]:
    now = datetime.now(timezone.utc)
    record = SessionRecord(
        actor_id="mina.teacher",
        display_name="Mina Teacher",
        sub="sub-multiworker",
        kc_sid="kc-multiworker",
        created_at=now,
        expires_at=now + timedelta(hours=1),
        refresh_token="rt",
        id_token="idt",
        csrf_token="csrf-token",
    )
    return {COOKIE_NAME: SessionCookieCodec(COOKIE_SECRET).encode(record)}


@pytest.fixture(scope="module")
def two_servers(tmp_path_factory: pytest.TempPathFactory) -> Iterator[tuple[_Server, _Server]]:
    logs = tmp_path_factory.mktemp("gunicorn")
    servers = (_Server(1, logs / "first.log"), _Server(1, logs / "second.log"))
    try:
        for server in servers:
            server.wait_until_serving()
        yield servers
    finally:
        for server in servers:
            server.stop()


@pytest.fixture(scope="module")
def multi_worker_server(tmp_path_factory: pytest.TempPathFactory) -> Iterator[_Server]:
    server = _Server(2, tmp_path_factory.mktemp("gunicorn") / "workers.log")
    try:
        server.wait_until_serving()
        yield server
    finally:
        server.stop()


def test_a_cookie_is_accepted_by_a_process_that_never_issued_it(
    two_servers: tuple[_Server, _Server], session_cookie: dict[str, str]
):
    for server in two_servers:
        response = server.get(session_cookie)
        assert response.status_code == 303
        assert response.headers["location"] == f"{FRONTEND_PREFIX}/users"


def test_a_request_without_a_cookie_is_sent_to_the_login(two_servers: tuple[_Server, _Server]):
    response = two_servers[0].get()
    assert response.status_code == 303
    assert "/auth/login" in response.headers["location"]


def test_every_worker_of_one_master_accepts_the_same_cookie(
    multi_worker_server: _Server, session_cookie: dict[str, str]
):
    assert multi_worker_server.booted_workers() == 2
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(multi_worker_server.get, session_cookie) for _ in range(24)]
        responses = [future.result() for future in futures]
    assert [response.status_code for response in responses] == [303] * 24
    assert {response.headers["location"] for response in responses} == {f"{FRONTEND_PREFIX}/users"}
