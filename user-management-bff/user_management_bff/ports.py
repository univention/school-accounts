# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine, Generic, TypeVar

from fastapi import Request

from .models import Permission, School, Target, User


class UsersPersistencePort(ABC):
    @abstractmethod
    async def get_users(self, school: str) -> list[User]:  # pragma: no cover
        ...

    @abstractmethod
    async def get_user(self, identifier: str) -> User:  # pragma: no cover
        """
        This method returns the user, which is identified by identifier.

        Raises an ObjectNotFoundError, if the user could not be found.q
        """


class SchoolsPersistencePort(ABC):
    @abstractmethod
    async def get_schools(self) -> list[School]:  # pragma: no cover
        ...


UsersGetRepresentation = TypeVar("UsersGetRepresentation")


class UsersRepresentationPort(ABC, Generic[UsersGetRepresentation]):
    @abstractmethod
    def create_users_representation(
        self, users: list[User]
    ) -> UsersGetRepresentation:  # pragma: no cover
        ...


SchoolsGetRepresentation = TypeVar("SchoolsGetRepresentation")


class SchoolsRepresentationPort(ABC, Generic[SchoolsGetRepresentation]):
    @abstractmethod
    def create_schools_representation(
        self, schools: list[School], permissions: dict[str, list[Permission]]
    ) -> SchoolsGetRepresentation:  # pragma: no cover
        ...


class FastAPIAuthenticationPort(ABC):

    @abstractmethod
    async def get_authentication_dependency(
        self,
    ) -> Callable[[], Coroutine[Any, Any, str]]:  # pragma: no cover
        """
        This function should return a FastAPI dependency for authentication.

        The returned dependency should either raise an exception
        or return the authenticated users' identifier
        """

    @abstractmethod
    async def get_authenticated_id(self, request: Request) -> str:
        """
        This method authenticates the provided request and returns the identifier
        of the authenticated user.

        If no user can be authenticated, a HTTException with status code 403 should be raised.
        """


class PermissionsPort(ABC):
    @abstractmethod
    async def get_permissions(self, actor: User, targets: list[Target]) -> dict[str, list[Permission]]:
        """
        This method returns the permissions the provided actor has on the given targets.
        """
