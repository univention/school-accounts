# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from .models import User


class UsersPersistencePort(ABC):
    @abstractmethod
    def get_users(self, school: str) -> list[User]:  # pragma: no cover
        ...


UsersGetRepresentation = TypeVar("UsersGetRepresentation")


class UsersRepresentationPort(ABC, Generic[UsersGetRepresentation]):
    @abstractmethod
    def create_users_representation(
        self, users: list[User]
    ) -> UsersGetRepresentation:  # pragma: no cover
        ...
