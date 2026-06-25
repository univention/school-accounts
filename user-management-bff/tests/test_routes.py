# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
"""Tests for the UI router (serves the server-rendered HTML/HTMX shell)."""
from user_management_bff.constants import FRONTEND_PREFIX


def test_shell_renders(test_client):
    response = test_client.get(FRONTEND_PREFIX)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    # Application shell built from the design system.
    assert "<html" in body
    assert "data-theme" in body
    assert "<u-page" in body
    # Vendored assets are referenced from the static mount.
    assert "vendor/univention-design-system.js" in body
    assert "vendor/htmx.min.js" in body
    assert "vendor/alpine.min.js" in body
