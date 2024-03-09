# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import pytest

from user_management_bff.business_logic import get_schools
from user_management_bff.errors import NoSchoolUserError, ObjectNotFoundError


@pytest.mark.asyncio
async def test_get_schools_actor_not_found(mocker):
    users_get_mock = mocker.AsyncMock()
    users_get_mock.get_user.side_effect = ObjectNotFoundError(identifier="USER")
    with pytest.raises(
        NoSchoolUserError, match="The logged in user 'USER' is not a valid UCS@school user."
    ) as exc_info:
        await get_schools(
            mocker.AsyncMock(), mocker.AsyncMock(), mocker.AsyncMock(), users_get_mock, "USER"
        )
    assert exc_info.value.identifier == "USER"
