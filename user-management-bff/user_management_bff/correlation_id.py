# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
from contextvars import ContextVar

correlation_id_ctx_var: ContextVar = ContextVar("correlation_id")
