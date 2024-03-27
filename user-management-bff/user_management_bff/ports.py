# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine, Generic, Optional, TypeVar

from fastapi import Request

from .api_models import EditUserResponseUser, UserCreateRequest
from .models import Permission, School, SchoolClass, Target, User


class UsersPersistencePort(ABC):
    @abstractmethod
    async def get_users(self, school: str) -> list[User]:  # pragma: no cover
        ...

    @abstractmethod
    async def get_user(self, identifier: str) -> User:  # pragma: no cover
        """
        This method returns the user, which is identified by identifier.

        Raises an ObjectNotFoundError, if the user could not be found.
        """

    @abstractmethod
    async def create_user(self, user: UserCreateRequest) -> User:  # pragma: no cover
        ...

    @abstractmethod
    async def delete_user(self, identifier: str) -> None:  # pragma: no cover
        """
        This method deletes the user, which is identified by identifier.

        Raises an ObjectNotFoundError, if the user could not be found.
        """

    @abstractmethod
    async def save_user(self, user: User) -> User:  # pragma: no cover
        """
        This method saves a given user.

        Raises ObjectNotFoundError, if the user could not be found.
        """


class SchoolsPersistencePort(ABC):
    @abstractmethod
    async def get_schools(self, name: Optional[str] = None) -> list[School]:  # pragma: no cover
        ...


class SchoolClassesPersistencePort(ABC):
    @abstractmethod
    async def get_school_classes(self, school: str) -> list[SchoolClass]:
        """
        This method returns all school classes of a given school.
        """


UsersGetRepresentation = TypeVar("UsersGetRepresentation")
UserCreateRepresentation = TypeVar("UserCreateRepresentation")


class UsersRepresentationPort(ABC, Generic[UsersGetRepresentation, UserCreateRepresentation]):
    @abstractmethod
    def create_users_representation(
        self, users: list[User], permissions: dict[str, list[Permission]]
    ) -> UsersGetRepresentation:  # pragma: no cover
        ...

    @abstractmethod
    def create_user_representation(
        self, user: User, permissions: set[Permission]
    ) -> UserCreateRepresentation:  # pragma: no cover
        ...

    @abstractmethod
    def edit_user_representation(
        self, user: User, permissions: set[Permission]
    ) -> EditUserResponseUser: ...


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


ListUsersConfigRepresentation = TypeVar("ListUsersConfigRepresentation")


class ListConfigRepresentationPort(ABC, Generic[ListUsersConfigRepresentation]):
    @abstractmethod
    def list_config_representation(self, lang: str = "en") -> ListUsersConfigRepresentation: ...


AddUserConfigRepresentation = TypeVar("AddUserConfigRepresentation")


class AddConfigRepresentationPort(ABC, Generic[AddUserConfigRepresentation]):
    @abstractmethod
    def add_config_representation(
        self, school: School, school_classes: list[SchoolClass], lang: str
    ) -> AddUserConfigRepresentation: ...


EditUserConfigRepresentation = TypeVar("EditUserConfigRepresentation")


class EditConfigRepresentationPort(ABC, Generic[EditUserConfigRepresentation, UserCreateRepresentation]):
    @abstractmethod
    def edit_config_representation(
        self,
        user_data: UserCreateRepresentation,
        school: School,
        school_classes: list[SchoolClass],
        lang: str,
    ) -> EditUserConfigRepresentation: ...
