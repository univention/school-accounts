# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import pytest

from user_management_bff.api_models import UserCreateRequest
from user_management_bff.business_logic import create_user, get_schools, user_create_request_to_target
from user_management_bff.errors import NoSchoolUserError, ObjectNotFoundError
from user_management_bff.lang import _
from user_management_bff.models import Role, Target, TargetObject, TargetObjectType


@pytest.fixture
def users_get_not_found_mock(mocker):
    users_get_mock = mocker.AsyncMock()
    users_get_mock.get_user.side_effect = ObjectNotFoundError(identifier="USER")
    return users_get_mock


@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["en", "de"])
async def test_get_schools_actor_not_found(mocker, users_get_not_found_mock, lang):
    user = "USER"
    with pytest.raises(
        NoSchoolUserError,
        match=_(f"The logged in user '{user}' is not a valid UCS@school user.", lang=lang),
    ) as exc_info:
        await get_schools(
            mocker.AsyncMock(),
            mocker.AsyncMock(),
            mocker.AsyncMock(),
            users_get_not_found_mock,
            "USER",
            lang,
        )
    assert exc_info.value.identifier == "USER"


@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["en", "de"])
async def test_create_user_actor_not_found(mocker, users_get_not_found_mock, lang):
    user = "USER"
    with pytest.raises(
        NoSchoolUserError,
        match=_(f"The logged in user '{user}' is not a valid UCS@school user.", lang=lang),
    ) as exc_info:
        await create_user(
            mocker.MagicMock(),
            mocker.MagicMock(),
            users_get_not_found_mock,
            mocker.MagicMock(),
            "USER",
            mocker.MagicMock(),
            lang,
        )
    assert exc_info.value.identifier == "USER"


def test_user_create_request_to_target():
    user = UserCreateRequest(
        last_name="Mustermann",
        first_name="Max",
        username="max.mustermann",
        password="univention",
        school="school1",
        school_classes=["1a"],
        roles=[Role.TEACHER],
        disabled=False,
    )
    expected = Target(
        old_target=None,
        new_target=TargetObject(
            id="max.mustermann",
            type=TargetObjectType.USER,
            attributes=dict(
                last_name="Mustermann",
                first_name="Max",
                username="max.mustermann",
                password="univention",
                schools=["school1"],
                school_classes={"school1": ["1a"]},
                roles=["teacher:school:school1"],
                activated=True,
            ),
        ),
    )
    assert user_create_request_to_target(user) == expected
