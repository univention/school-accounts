# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from os import getenv
from typing import Callable, Optional

import pytest
import pytest_asyncio
from authlib.integrations.requests_client import OAuth2Session
from ucsschool.kelvin.client import NoObject, SchoolClass, SchoolClassResource, Session, UserResource
from ucsschool.kelvin.client import User as KelvinUser


@pytest.fixture(scope="session")
def base_url(pytestconfig):
    return pytestconfig.getoption("base_url")


@pytest.fixture(scope="session")
def guardian_management_url(pytestconfig):
    return pytestconfig.getoption("guardian_management_url")


@pytest.fixture(scope="session")
def kelvin_url(pytestconfig):
    return pytestconfig.getoption("kelvin_url")


@pytest.fixture(scope="session", autouse=True)
def browser_context_args(browser_context_args):
    return {**browser_context_args, "ignore_https_errors": True}


@pytest.fixture
def access_token() -> Callable[[str, str], str]:
    def wrapper(username: str, password: str) -> str:
        client = OAuth2Session(client_id="ucsschool-user-management-test", client_secret="univention")
        token = client.fetch_token(
            "https://ucs-sso-ng.school.test/realms/ucs/protocol/openid-connect/token",
            username=username,
            password=password,
        )
        return token["access_token"]

    return wrapper


@pytest.fixture(scope="session")
def kelvin_credentials(kelvin_url):
    return {"username": "Administrator", "password": "univention", "host": kelvin_url}


@pytest_asyncio.fixture
async def kelvin_user_deletion(kelvin_credentials) -> Callable[[str], None]:
    to_delete = set()

    def _add_to_delete_list(username):
        to_delete.add(username)

    yield _add_to_delete_list
    async with Session(**kelvin_credentials) as session:
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
    ):
        first_name = faker.first_name()
        last_name = faker.last_name()
        async with Session(**kelvin_credentials) as session:
            user = KelvinUser(
                name=f"{first_name}.{last_name}",
                firstname=first_name,
                lastname=last_name,
                record_uid=f"{first_name}.{last_name}",
                school=school,
                schools=schools,
                roles=roles,
                school_classes=school_classes if school_classes is not None else {},
                session=session,
            )
            result = await user.save()
            kelvin_user_deletion(result.name)
            return result

    return _kelvin_user_factory


@pytest_asyncio.fixture
async def kelvin_school_class_deletion(kelvin_credentials) -> Callable[[str], None]:
    to_delete = set()

    def _add_to_delete_list(school, name):
        to_delete.add((school, name))

    yield _add_to_delete_list
    async with Session(**kelvin_credentials) as session:
        for school, name in to_delete:
            try:
                school_class = await SchoolClassResource(session=session).get(school=school, name=name)
                await school_class.delete()
            except NoObject:
                pass


@pytest.fixture
def kelvin_school_class_factory(kelvin_credentials, kelvin_school_class_deletion, faker):
    async def _kelvin_school_class_factory(
        *,
        school: str,
        name: str,
    ):
        async with Session(**kelvin_credentials) as session:
            school_class = SchoolClass(
                name=name,
                school=school,
                users=[],
                session=session,
            )
            result = await school_class.save()
            kelvin_school_class_deletion(school=school, name=name)
            return result

    return _kelvin_school_class_factory


@pytest.fixture
def get_kelvin_user(kelvin_credentials):
    async def _get_kelvin_user(username):
        async with Session(**kelvin_credentials) as session:
            return await UserResource(session=session).get(name=username)

    return _get_kelvin_user


@pytest.fixture
def kelvin_session():
    username = getenv("KELVIN_PERSISTENCE_ADAPTER__USERNAME")
    if not username:
        with open(getenv("KELVIN_PERSISTENCE_ADAPTER__USERNAME_FILE")) as f:
            username = f.read().strip()
    password = getenv("KELVIN_PERSISTENCE_ADAPTER__PASSWORD")
    if not password:
        with open(getenv("KELVIN_PERSISTENCE_ADAPTER__PASSWORD_FILE")) as f:
            password = f.read().strip()
    return Session(
        username=username,
        password=password,
        host=getenv("KELVIN_PERSISTENCE_ADAPTER__URL"),
        verify=getenv("SSL_CERT_FILE"),
    )
