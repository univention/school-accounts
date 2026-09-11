# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Encoding of the self-contained session cookie.

Encrypted and not merely signed: the payload carries the refresh token, which
stays usable against Keycloak for its own lifetime no matter what the cookie's
``max_age`` says.
"""

from __future__ import annotations

import base64
import zlib

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from loguru import logger
from pydantic import BaseModel, ValidationError

from user_management_bff.models import SessionRecord

# Bump whenever a change to SessionRecord makes an older payload unreadable.
COOKIE_VERSION = 1

_HKDF_INFO = b"user-management-session-v1"

# Browsers drop a cookie over 4096 bytes; the rest is headroom for the UCS proxy's own limits.
_MAX_COOKIE_BYTES = 3800


class _CookiePayload(BaseModel):
    version: int
    session: SessionRecord


def _derive_key(secret: str) -> bytes:
    # The same secret keys Starlette's OAuth-state cookie; deriving keeps the two uses apart.
    derived = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=_HKDF_INFO).derive(
        secret.encode("utf-8")
    )
    return base64.urlsafe_b64encode(derived)


class SessionCookieCodec:
    def __init__(self, secret: str) -> None:
        self._fernet: Fernet = Fernet(_derive_key(secret))

    def encode(self, record: SessionRecord) -> str:
        payload = _CookiePayload(version=COOKIE_VERSION, session=record)
        # Without deflating first, a payload holding both tokens exceeds the cookie size limit.
        compressed = zlib.compress(payload.model_dump_json().encode("utf-8"))
        token = self._fernet.encrypt(compressed).decode("ascii")
        if len(token) > _MAX_COOKIE_BYTES:
            logger.error(
                "The session cookie is too large for browsers to keep; sessions will not persist. "
                "Usually the ID token carries too many claims - trim the Keycloak client's mappers.",
                actor_id=record.actor_id,
                size=len(token),
                limit=_MAX_COOKIE_BYTES,
            )
        return token

    def decode(self, raw: str) -> SessionRecord | None:
        try:
            plain = zlib.decompress(self._fernet.decrypt(raw.encode("ascii")))
        except (InvalidToken, zlib.error, UnicodeEncodeError):
            logger.info(
                "Rejected a session cookie that could not be decrypted, so this user has to log "
                "in again. Usually follows a change of the session secret.",
            )
            return None
        try:
            payload = _CookiePayload.model_validate_json(plain)
        except ValidationError:
            logger.info(
                "Rejected a session cookie whose payload could not be read, so this user has to "
                "log in again. Usually follows a release that changed the cookie without its version.",
            )
            return None
        if payload.version != COOKIE_VERSION:
            logger.warning(
                "Session cookie predates the running release; requiring re-login. "
                "Expected once per session after an app update, no action needed.",
                cookie_version=payload.version,
                expected_version=COOKIE_VERSION,
            )
            return None
        return payload.session
