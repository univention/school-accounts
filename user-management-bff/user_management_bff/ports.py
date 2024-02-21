# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine, Generic, TypeVar

from .models import School, User


class UsersPersistencePort(ABC):
    @abstractmethod
    async def get_users(self, school: str) -> list[User]:  # pragma: no cover
        ...


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
        self, schools: list[School]
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
