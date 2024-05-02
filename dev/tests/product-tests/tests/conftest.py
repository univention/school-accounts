# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
import time
from typing import Callable, Optional

import nest_asyncio
import pytest
import os

import pytest_asyncio
from playwright.sync_api import Page, expect
from ucsschool.kelvin.client import Session, UserResource, NoObject, User

nest_asyncio.apply()


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "ignore_https_errors": True}


@pytest.fixture
def page_login(page: Page) -> Callable[[str, str], Page]:
    def wrapper(username: str, password: str) -> Page:
        if os.getenv("CI_INTEGRATION"):
            page.goto("/univention/ucsschool/user-management/ui/")
        page.get_by_label("Username or email").fill(username)
        page.get_by_label("Password", exact=True).fill(password)
        page.get_by_label("Password", exact=True).press("Enter")
        expect(page.get_by_role("heading", name="Users (schools)")).to_be_visible(timeout=10000)

        return page

    return wrapper


@pytest.fixture(scope="session")
def kelvin_url():
    return "primary.school.test"


@pytest.fixture(scope="session")
def kelvin_credentials(kelvin_url):
    return {"username": "Administrator", "password": "univention", "host": kelvin_url}


@pytest_asyncio.fixture
async def kelvin_user_deletion(kelvin_credentials) -> Callable[[str], None]:
    to_delete = set()

    def _add_to_delete_list(username):
        to_delete.add(username)

    yield _add_to_delete_list
    async with Session(**kelvin_credentials, verify=False) as session:
        for username in to_delete:
            try:
                user = await UserResource(session=session).get(name=username)
                await user.delete()
            except NoObject:
                pass


@pytest.fixture
def kelvin_user_factory(kelvin_credentials, kelvin_user_deletion, faker):
    async def _kelvin_user_factory(
        *,
        school: str,
        schools: list[str],
        roles: list[str],
        school_classes: Optional[dict[str, list[str]]] = None,
        password: Optional[str] = None,
        delete_after_test: bool = True,
    ):
        first_name = faker.first_name()
        last_name = faker.last_name()
        async with Session(**kelvin_credentials, verify=False) as session:
            user = User(
                name=f"{int(time.time())}",
                firstname=first_name,
                lastname=last_name,
                record_uid=f"{first_name}.{last_name}",
                school=school,
                schools=schools,
                roles=roles,
                school_classes=school_classes if school_classes is not None else {},
                session=session,
            )
            if password is not None:
                user.password = password
            result = await user.save()
            # If the username is changed in the test, we have to delete it in the test, not here.
            if delete_after_test:
                kelvin_user_deletion(result.name)
            return result

    return _kelvin_user_factory
