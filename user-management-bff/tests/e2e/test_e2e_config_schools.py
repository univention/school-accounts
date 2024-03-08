# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import pytest
import requests


@pytest.mark.parametrize(
    "username,expected_permissions", [("mina.teacher", []), ("max.student", []), ("alex.admin", [])]
)
@pytest.mark.e2e
def test_config_schools_permissions(access_token, base_url, username, expected_permissions):
    token = access_token(username, "univention")
    response = requests.get(
        f"{base_url}/bff/config-schools", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "schools": [
            {"label": school_label, "value": school_name, "permissions": expected_permissions}
            for school_label, school_name in [
                ("Demo School", "DEMOSCHOOL"),
                ("school1", "school1"),
                ("school2", "school2"),
            ]
        ]
    }
