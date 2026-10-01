# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
from contextvars import ContextVar

correlation_id_ctx_var: ContextVar[str] = ContextVar("correlation_id")
