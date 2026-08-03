# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine

from fastapi import Request
from starlette.responses import RedirectResponse, Response

from .constants import FRONTEND_PREFIX
from .models import Permission, School, SchoolClass, SessionRecord, Target, User, WorkGroup


class UsersPersistencePort(ABC):
    @abstractmethod
    async def get_users(
        self, school: str, school_classes: list[str], work_groups: list[str]
    ) -> list[User]:  # pragma: no cover
        ...

    @abstractmethod
    async def get_user(self, identifier: str) -> User:  # pragma: no cover
        """
        This method returns the user, which is identified by identifier.

        Raises an ObjectNotFoundError, if the user could not be found.
        """


class SchoolsPersistencePort(ABC):
    @abstractmethod
    async def get_schools(self, name: str | None = None) -> list[School]:  # pragma: no cover
        ...


class SchoolClassesPersistencePort(ABC):

    @abstractmethod
    async def get_school_classes(self, school: str) -> list[SchoolClass]:
        """
        This method returns all school classes of a given school.
        """


class WorkGroupsPersistencePort(ABC):

    @abstractmethod
    async def get_work_groups(self, school: str) -> list[WorkGroup]:
        """
        This method returns all work groups of a given school.
        """


class FastAPIAuthenticationPort(ABC):

    @abstractmethod
    async def get_authentication_dependency(
        self,
    ) -> Callable[..., Coroutine[Any, Any, str]]:  # pragma: no cover
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

        If no user can be authenticated, a ``NotAuthenticatedError`` is raised.
        """

    async def login_redirect(self, _request: Request, next_url: str = "") -> Response:
        """Start an interactive login, returning a redirect to the identity provider.

        The default implementation is a no-op redirect for adapters that do not
        implement an interactive flow (e.g. the dev/test doubles).
        """
        return RedirectResponse(next_url or FRONTEND_PREFIX, status_code=303)

    async def complete_login(self, _request: Request) -> Response:
        """Finish an interactive login (provider callback) and establish a session.

        The default implementation simply redirects to the application shell.
        """
        return RedirectResponse(FRONTEND_PREFIX, status_code=303)

    async def logout(self, _request: Request) -> Response:
        """End the current session and redirect away from the application.

        The default implementation simply redirects to the application shell.
        """
        return RedirectResponse(FRONTEND_PREFIX, status_code=303)


class SessionStorePort(ABC):
    """Storage for server-side authenticated sessions.

    Sessions are keyed by an opaque session id (returned by :meth:`create`).
    The ``kc_sid``/``sub`` lookups exist so sessions can be invalidated by the
    identity provider (e.g. OIDC back-channel logout) without the cookie.
    """

    @abstractmethod
    async def create(self, record: SessionRecord) -> str:  # pragma: no cover
        """Persist a new session and return its opaque session id."""

    @abstractmethod
    async def get(self, session_id: str) -> SessionRecord | None:  # pragma: no cover
        """Return the session for ``session_id``, or ``None`` if unknown."""

    @abstractmethod
    async def update(self, session_id: str, record: SessionRecord) -> None:  # pragma: no cover
        """Replace the session record for an existing ``session_id``."""

    @abstractmethod
    async def delete(self, session_id: str) -> None:  # pragma: no cover
        """Remove the session for ``session_id`` (no-op if unknown)."""

    @abstractmethod
    async def delete_by_kc_sid(self, kc_sid: str) -> None:  # pragma: no cover
        """Remove every session belonging to the given Keycloak session id."""

    @abstractmethod
    async def delete_by_sub(self, sub: str) -> None:  # pragma: no cover
        """Remove every session belonging to the given subject."""


class PermissionsPort(ABC):
    @abstractmethod
    async def get_permissions(self, actor: User, targets: list[Target]) -> dict[str, list[Permission]]:
        """
        This method returns the permissions the provided actor has on the given targets.
        """
