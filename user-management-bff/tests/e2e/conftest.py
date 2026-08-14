# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

from os import getenv
from typing import TYPE_CHECKING, Any, TypedDict, cast

import pytest
import pytest_asyncio
from authlib.integrations.requests_client import OAuth2Session
from ucsschool.kelvin.client import NoObject, SchoolClass, SchoolClassResource, Session, UserResource
from ucsschool.kelvin.client import User as KelvinUser

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Coroutine
    from typing import Callable

    from faker import Faker


class KelvinCredentials(TypedDict):
    username: str
    password: str
    host: str


@pytest.fixture(scope="session")
def base_url(pytestconfig: pytest.Config) -> str:
    return cast(str, pytestconfig.getoption("base_url"))


@pytest.fixture(scope="session")
def cerbos_url(pytestconfig: pytest.Config) -> str:
    return cast(str, pytestconfig.getoption("cerbos_url"))


@pytest.fixture(scope="session")
def kelvin_url(pytestconfig: pytest.Config) -> str:
    return cast(str, pytestconfig.getoption("kelvin_url"))


@pytest.fixture
def access_token() -> Callable[[str, str], str]:
    def wrapper(username: str, password: str) -> str:
        client = OAuth2Session(client_id="ucsschool-user-management-test", client_secret="univention")
        # authlib ships no types; fetch_token() returns an OAuth2Token, a plain dict subclass.
        token = cast(
            dict[str, Any],
            client.fetch_token(  # pyright: ignore[reportUnknownMemberType]
                "https://ucs-sso-ng.ucsschool.test/realms/ucs/protocol/openid-connect/token",
                username=username,
                password=password,
            ),
        )
        return token["access_token"]

    return wrapper


@pytest.fixture(scope="session")
def kelvin_credentials(kelvin_url: str) -> KelvinCredentials:
    return {"username": "Administrator", "password": "univention", "host": kelvin_url}


@pytest_asyncio.fixture  # pyright: ignore[reportUntypedFunctionDecorator]
async def kelvin_user_deletion(
    kelvin_credentials: KelvinCredentials,
) -> AsyncIterator[Callable[[str], None]]:
    to_delete: set[str] = set()

    def _add_to_delete_list(username: str) -> None:
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
def kelvin_user_factory(
    kelvin_credentials: KelvinCredentials,
    kelvin_user_deletion: Callable[[str], None],
    faker: Faker,
) -> Callable[..., Coroutine[Any, Any, KelvinUser]]:
    async def _kelvin_user_factory(
        *,
        school: str,
        schools: list[str],
        roles: list[str],
        school_classes: dict[str, list[str]] | None = None,
        work_groups: dict[str, list[str]] | None = None,
    ) -> KelvinUser:
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
                work_groups=work_groups if work_groups is not None else {},
                session=session,
            )
            result = cast(KelvinUser, await user.save())
            kelvin_user_deletion(result.name)
            return result

    return _kelvin_user_factory


@pytest_asyncio.fixture  # pyright: ignore[reportUntypedFunctionDecorator]
async def kelvin_school_class_deletion(
    kelvin_credentials: KelvinCredentials,
) -> AsyncIterator[Callable[[str, str], None]]:
    to_delete: set[tuple[str, str]] = set()

    def _add_to_delete_list(school: str, name: str) -> None:
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
def kelvin_school_class_factory(
    kelvin_credentials: KelvinCredentials,
    kelvin_school_class_deletion: Callable[[str, str], None],
    faker: Faker,
) -> Callable[..., Coroutine[Any, Any, SchoolClass]]:
    async def _kelvin_school_class_factory(
        *,
        school: str,
        name: str,
        description: str | None = None,
    ) -> SchoolClass:
        async with Session(**kelvin_credentials) as session:
            school_class = SchoolClass(
                name=name,
                school=school,
                # ucsschool.kelvin.client's SchoolClass declares description: str = None
                description=cast(str, description),
                users=[],
                session=session,
            )
            result = cast(SchoolClass, await school_class.save())
            kelvin_school_class_deletion(school, name)
            return result

    return _kelvin_school_class_factory


@pytest.fixture
def get_kelvin_user(
    kelvin_credentials: KelvinCredentials,
) -> Callable[[str], Coroutine[Any, Any, KelvinUser]]:
    async def _get_kelvin_user(username: str) -> KelvinUser:
        async with Session(**kelvin_credentials) as session:
            return await UserResource(session=session).get(name=username)

    return _get_kelvin_user


@pytest.fixture
def kelvin_session() -> Session:
    username = getenv("KELVIN_PERSISTENCE_ADAPTER__USERNAME")
    if not username:
        username_file = getenv("KELVIN_PERSISTENCE_ADAPTER__USERNAME_FILE")
        assert username_file, "KELVIN_PERSISTENCE_ADAPTER__USERNAME(_FILE) must be set"
        with open(username_file) as f:
            username = f.read().strip()
    password = getenv("KELVIN_PERSISTENCE_ADAPTER__PASSWORD")
    if not password:
        password_file = getenv("KELVIN_PERSISTENCE_ADAPTER__PASSWORD_FILE")
        assert password_file, "KELVIN_PERSISTENCE_ADAPTER__PASSWORD(_FILE) must be set"
        with open(password_file) as f:
            password = f.read().strip()
    host = getenv("KELVIN_PERSISTENCE_ADAPTER__URL")
    assert host, "KELVIN_PERSISTENCE_ADAPTER__URL must be set"
    return Session(
        username=username,
        password=password,
        host=host,
        verify=getenv("SSL_CERT_FILE"),
    )
