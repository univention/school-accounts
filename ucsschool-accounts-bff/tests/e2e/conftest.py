# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

from dataclasses import dataclass
from os import getenv
from typing import TYPE_CHECKING, Any, TypedDict, cast

import pytest
import pytest_asyncio
from authlib.integrations.requests_client import OAuth2Session
from ucsschool.kelvin.client import NoObject, SchoolClass, SchoolClassResource, Session, UserResource
from ucsschool.kelvin.client import User as KelvinUser

from ucsschool_accounts_bff.adapters.base import (
    KelvinPersistenceAdapterSettings,
    _SessionHolder,
    enter_session_scope,
)
from ucsschool_accounts_bff.adapters.permissions import (
    CerbosPermissionsAdapter,
    CerbosPermissionsAdapterSettings,
)
from ucsschool_accounts_bff.adapters.school_classes import KelvinSchoolClassesPersistenceAdapter
from ucsschool_accounts_bff.adapters.schools import KelvinSchoolsPersistenceAdapter
from ucsschool_accounts_bff.adapters.users import KelvinUsersPersistenceAdapter
from ucsschool_accounts_bff.adapters.work_groups import KelvinWorkGroupsPersistenceAdapter

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Coroutine, Iterator
    from typing import Callable

    from faker import Faker


class KelvinCredentials(TypedDict):
    username: str
    password: str
    host: str


@dataclass
class KelvinPorts:
    """The Kelvin-backed persistence adapters, ready to hand to `business_logic`."""

    users: KelvinUsersPersistenceAdapter
    schools: KelvinSchoolsPersistenceAdapter
    school_classes: KelvinSchoolClassesPersistenceAdapter
    work_groups: KelvinWorkGroupsPersistenceAdapter


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
        client = OAuth2Session(client_id="ucsschool-accounts-test", client_secret="univention")
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
        legal_guardians: list[str] | None = None,
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
                # Kelvin rejects this on anything but a student, and caps it at 4.
                legal_guardians=legal_guardians if legal_guardians is not None else [],
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


def _kelvin_secret(name: str) -> str:
    """Read a KELVIN_PERSISTENCE_ADAPTER__ setting from the env or its _FILE variant."""
    value = getenv(f"KELVIN_PERSISTENCE_ADAPTER__{name}")
    if not value:
        path = getenv(f"KELVIN_PERSISTENCE_ADAPTER__{name}_FILE")
        assert path, f"KELVIN_PERSISTENCE_ADAPTER__{name}(_FILE) must be set"
        with open(path) as f:
            value = f.read().strip()
    return value


@pytest_asyncio.fixture  # pyright: ignore[reportUnknownMemberType, reportUntypedFunctionDecorator]
async def cerbos_adapter(cerbos_url: str) -> CerbosPermissionsAdapter:
    adapter = CerbosPermissionsAdapter()
    await adapter.configure(CerbosPermissionsAdapterSettings(cerbos_target=cerbos_url, tls_verify=False))
    return adapter


@pytest.fixture
def kelvin_adapter_settings() -> KelvinPersistenceAdapterSettings:
    """The settings the app itself runs the Kelvin adapters with, read from its env."""
    host = getenv("KELVIN_PERSISTENCE_ADAPTER__URL")
    assert host, "KELVIN_PERSISTENCE_ADAPTER__URL must be set"
    return KelvinPersistenceAdapterSettings(
        url=host,
        username=_kelvin_secret("USERNAME"),
        password=_kelvin_secret("PASSWORD"),
    )


@pytest.fixture
def kelvin_session(kelvin_adapter_settings: KelvinPersistenceAdapterSettings) -> Session:
    return Session(
        username=kelvin_adapter_settings.username,
        password=kelvin_adapter_settings.password,
        host=kelvin_adapter_settings.url,
        verify=getenv("SSL_CERT_FILE"),
    )


@pytest.fixture(autouse=True)
def kelvin_scope() -> Iterator[_SessionHolder]:
    """The router opens a scope per request; a test driving the adapters needs one too.

    Sync on purpose: pytest-asyncio runs an async fixture in a different context
    from the test, so a ContextVar set there never reaches the test body.
    """
    with enter_session_scope() as holder:
        yield holder


@pytest_asyncio.fixture(autouse=True)  # pyright: ignore[reportUnknownMemberType, reportUntypedFunctionDecorator]
async def close_kelvin_session(kelvin_scope: _SessionHolder) -> AsyncIterator[None]:
    """These adapters reach a real Kelvin, so the session has to be closed again."""
    yield
    if kelvin_scope.session is not None:
        await kelvin_scope.session.close()


@pytest_asyncio.fixture  # pyright: ignore[reportUnknownMemberType, reportUntypedFunctionDecorator]
async def kelvin_ports(
    kelvin_adapter_settings: KelvinPersistenceAdapterSettings,
) -> KelvinPorts:
    """The persistence adapters `business_logic` is driven with in production."""
    users = KelvinUsersPersistenceAdapter()
    schools = KelvinSchoolsPersistenceAdapter()
    school_classes = KelvinSchoolClassesPersistenceAdapter()
    work_groups = KelvinWorkGroupsPersistenceAdapter()
    for adapter in (users, schools, school_classes, work_groups):
        await adapter.configure(kelvin_adapter_settings)
    return KelvinPorts(
        users=users, schools=schools, school_classes=school_classes, work_groups=work_groups
    )
