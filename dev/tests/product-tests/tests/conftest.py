# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
import time
from typing import Callable
from urllib.parse import urlparse

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
        page.goto("/univention/ucsschool/user-management/ui/")
        if os.getenv("CI_INTEGRATION"):
            page.get_by_label("Username or email").fill(username)
            page.get_by_label("Password", exact=True).fill(password)
            page.get_by_label("Password", exact=True).press("Enter")
        expect(page.get_by_role("heading", name="Users (schools)")).to_be_visible(
            timeout=10000
        )

        return page

    return wrapper


@pytest.fixture
def admin_login() -> dict:
    return {"username": "alex.admin", "password": "univention"}


@pytest.fixture
def teacher_login() -> dict:
    return {"username": "mina.teacher", "password": "univention"}


def pytest_addoption(parser):
    parser.addoption("--kelvin_url", action="store")


@pytest.fixture(scope="session")
def kelvin_url(base_url, pytestconfig):
    kelvin_url = pytestconfig.getoption(
        "kelvin_url", default=urlparse(base_url).hostname
    )
    return kelvin_url


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
        school_classes: dict[str, list[str]] | None = None,
        password: str | None = None,
    ):
        first_name = faker.first_name()
        last_name = faker.last_name()
        async with Session(**kelvin_credentials, verify=False) as session:
            user = User(
                name=f"t{int(time.time())}",
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
            kelvin_user_deletion(result.name)
            return result

    return _kelvin_user_factory
