# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
from datetime import datetime, timezone

import pytest

from user_management_bff.adapters.session_store import InMemorySessionStoreAdapter
from user_management_bff.models import SessionRecord


def _record(**overrides: object) -> SessionRecord:
    base = SessionRecord(
        actor_id="mina.teacher",
        sub="sub-1",
        kc_sid="kc-1",
        expires_at=datetime(2999, 1, 1, tzinfo=timezone.utc),
        refresh_token="rt",
        id_token="idt",
        csrf_token="csrf-token",
    )
    return base.model_copy(update=overrides)


class TestInMemorySessionStoreAdapter:
    @pytest.fixture
    def store(self) -> InMemorySessionStoreAdapter:
        return InMemorySessionStoreAdapter()

    @pytest.mark.asyncio
    async def test_create_returns_opaque_id_and_persists(self, store: InMemorySessionStoreAdapter):
        record = _record()
        session_id = await store.create(record)
        assert isinstance(session_id, str) and session_id
        assert await store.get(session_id) == record

    @pytest.mark.asyncio
    async def test_create_generates_unique_ids(self, store: InMemorySessionStoreAdapter):
        first = await store.create(_record())
        second = await store.create(_record())
        assert first != second

    @pytest.mark.asyncio
    async def test_get_unknown_returns_none(self, store: InMemorySessionStoreAdapter):
        assert await store.get("nope") is None

    @pytest.mark.asyncio
    async def test_update_existing(self, store: InMemorySessionStoreAdapter):
        session_id = await store.create(_record())
        updated = _record(actor_id="other")
        await store.update(session_id, updated)
        assert (await store.get(session_id)).actor_id == "other"

    @pytest.mark.asyncio
    async def test_update_unknown_is_noop(self, store: InMemorySessionStoreAdapter):
        await store.update("nope", _record())
        assert await store.get("nope") is None

    @pytest.mark.asyncio
    async def test_delete(self, store: InMemorySessionStoreAdapter):
        session_id = await store.create(_record())
        await store.delete(session_id)
        assert await store.get(session_id) is None

    @pytest.mark.asyncio
    async def test_delete_unknown_is_noop(self, store: InMemorySessionStoreAdapter):
        await store.delete("nope")  # must not raise

    @pytest.mark.parametrize("field,method", [("kc_sid", "delete_by_kc_sid"), ("sub", "delete_by_sub")])
    @pytest.mark.asyncio
    async def test_delete_by_identity_removes_matching_only(
        self, store: InMemorySessionStoreAdapter, field: str, method: str
    ):
        keep = await store.create(_record(**{field: "other"}))
        drop = await store.create(_record(**{field: "target"}))
        await getattr(store, method)("target")
        assert await store.get(drop) is None
        assert await store.get(keep) is not None
