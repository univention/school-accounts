# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import base64
import random
import zlib
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.fernet import Fernet

from user_management_bff.models import SessionRecord
from user_management_bff.session_cookie import (
    COOKIE_VERSION,
    SessionCookieCodec,
    _CookiePayload,
    _derive_key,
)

SECRET = "5d41402abc4b2a76b9719d911017c5925d41402abc4b2a76b9719d911017c592"


def _record(**overrides: object) -> SessionRecord:
    now = datetime.now(timezone.utc)
    base = SessionRecord(
        actor_id="mina.teacher",
        display_name="Mina Teacher",
        sub="sub-1",
        kc_sid="kc-1",
        created_at=now,
        expires_at=now + timedelta(minutes=5),
        refresh_token="rt",
        id_token="idt",
        csrf_token="csrf-token",
    )
    return base.model_copy(update=overrides)


@pytest.fixture
def codec() -> SessionCookieCodec:
    return SessionCookieCodec(SECRET)


def test_round_trip_preserves_every_field(codec: SessionCookieCodec):
    record = _record()
    assert codec.decode(codec.encode(record)) == record


def test_cookie_value_leaks_no_plaintext(codec: SessionCookieCodec):
    token = codec.encode(_record(refresh_token="SECRET-REFRESH-TOKEN"))
    assert "SECRET-REFRESH-TOKEN" not in token
    assert "mina.teacher" not in token


def test_deflating_keeps_a_two_token_session_inside_the_cookie_limit(codec: SessionCookieCodec):
    # Both tokens at a realistic Keycloak size.
    jwt = base64.urlsafe_b64encode(b"x" * 900).decode()
    token = codec.encode(_record(refresh_token=jwt, id_token=jwt))
    assert len(token) < 4096


def test_another_secret_cannot_read_the_cookie(codec: SessionCookieCodec):
    other = SessionCookieCodec("0" * 64)
    assert other.decode(codec.encode(_record())) is None


def test_derive_key_is_deterministic_and_secret_specific():
    assert _derive_key(SECRET) == _derive_key(SECRET)
    assert _derive_key(SECRET) != _derive_key("0" * 64)


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "garbage",
        "gAAAAABn-not-a-real-token",
        "not-ascii-é",
    ],
)
def test_unreadable_cookie_is_rejected(codec: SessionCookieCodec, raw: str):
    assert codec.decode(raw) is None


def test_tampered_cookie_is_rejected(codec: SessionCookieCodec):
    token = codec.encode(_record())
    flipped = "A" if token[-2] != "A" else "B"
    assert codec.decode(token[:-2] + flipped + token[-1]) is None


def test_authentic_ciphertext_that_is_not_deflated_is_rejected(codec: SessionCookieCodec):
    fernet = Fernet(_derive_key(SECRET))
    assert codec.decode(fernet.encrypt(b"not compressed").decode("ascii")) is None


def test_payload_that_is_not_a_session_is_rejected(codec: SessionCookieCodec):
    fernet = Fernet(_derive_key(SECRET))
    raw = zlib.compress(b'{"version": 1, "session": {"actor_id": "x"}}')
    assert codec.decode(fernet.encrypt(raw).decode("ascii")) is None


def test_cookie_from_another_payload_version_is_rejected(codec: SessionCookieCodec):
    fernet = Fernet(_derive_key(SECRET))
    payload = _CookiePayload(version=COOKIE_VERSION + 1, session=_record())
    raw = zlib.compress(payload.model_dump_json().encode("utf-8"))
    assert codec.decode(fernet.encrypt(raw).decode("ascii")) is None


def test_oversized_cookie_still_encodes(codec: SessionCookieCodec):
    """The size guard logs, it does not raise."""
    # Seeded random bytes, so the payload is incompressible and reproducible.
    huge = base64.urlsafe_b64encode(random.Random(0).randbytes(6000)).decode()
    token = codec.encode(_record(refresh_token=huge))
    assert len(token) > 3800
    assert codec.decode(token) is not None
