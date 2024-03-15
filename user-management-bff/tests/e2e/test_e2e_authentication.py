# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import pytest
import requests


@pytest.mark.e2e
@pytest.mark.parametrize("username,expected_code", [("Administrator", 403), ("mina.teacher", 200)])
def test_no_school_user_login_fails(access_token, base_url, username, expected_code):
    token = access_token(username, "univention")
    response = requests.get(
        f"{base_url}/bff/config/schools", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == expected_code
