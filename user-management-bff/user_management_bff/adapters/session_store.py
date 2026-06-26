# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
"""Session storage adapters.

The in-memory adapter is sufficient for the single gunicorn worker the app
runs as today and needs no extra infrastructure. A Redis/DB-backed adapter can
be slotted in behind :class:`SessionStorePort` when horizontal scaling is
required, without touching the rest of the application.
"""
import secrets
from typing import Optional

from user_management_bff.models import SessionRecord
from user_management_bff.ports import SessionStorePort


class InMemorySessionStoreAdapter(SessionStorePort):

    class Config:
        alias = "in_memory"
        cached = True

    def __init__(self) -> None:
        self._store: dict[str, SessionRecord] = {}

    async def create(self, record: SessionRecord) -> str:
        session_id = secrets.token_urlsafe(32)
        self._store[session_id] = record
        return session_id

    async def get(self, session_id: str) -> Optional[SessionRecord]:
        return self._store.get(session_id)

    async def update(self, session_id: str, record: SessionRecord) -> None:
        if session_id in self._store:
            self._store[session_id] = record

    async def delete(self, session_id: str) -> None:
        self._store.pop(session_id, None)

    async def delete_by_kc_sid(self, kc_sid: str) -> None:
        for session_id in [sid for sid, rec in self._store.items() if rec.kc_sid == kc_sid]:
            del self._store[session_id]

    async def delete_by_sub(self, sub: str) -> None:
        for session_id in [sid for sid, rec in self._store.items() if rec.sub == sub]:
            del self._store[session_id]
