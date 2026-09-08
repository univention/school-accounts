# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from abc import ABC, abstractmethod
from collections.abc import Coroutine
from typing import Any, Callable

from fastapi import Request
from starlette.responses import RedirectResponse, Response

from .constants import FRONTEND_PREFIX
from .models import Permission, School, SchoolClass, Target, User, WorkGroup


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

    @abstractmethod
    async def set_password(self, identifier: str, password: str) -> None:  # pragma: no cover
        """
        Set ``password`` as the new password for the user identified by ``identifier``.

        Raises an ObjectNotFoundError, if the user could not be found, or a
        PasswordResetRejectedError, if the target system refuses the new password
        for this specific user (e.g. a Kelvin/UDM password-policy violation).
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

    # Async is required by the authentication port contract.
    async def login_redirect(  # NOSONAR(S7503)
        self,
        _request: Request,
        next_url: str = "",
    ) -> Response:
        """Start an interactive login, returning a redirect to the identity provider.

        The default implementation is a no-op redirect for adapters that do not
        implement an interactive flow (e.g. the dev/test doubles).
        """
        return RedirectResponse(next_url or FRONTEND_PREFIX, status_code=303)

    # Async is required by the authentication port contract.
    async def complete_login(  # NOSONAR(S7503)
        self,
        _request: Request,
    ) -> Response:
        """Finish an interactive login (provider callback) and establish a session.

        The default implementation simply redirects to the application shell.
        """
        return RedirectResponse(FRONTEND_PREFIX, status_code=303)

    # Async is required by the authentication port contract.
    async def logout(  # NOSONAR(S7503)
        self,
        _request: Request,
    ) -> Response:
        """End the current session and redirect away from the application.

        The default implementation simply redirects to the application shell.
        """
        return RedirectResponse(FRONTEND_PREFIX, status_code=303)

    # Async is required by the authentication port contract.
    async def issue_csrf_token(self, _request: Request) -> str:  # NOSONAR(S7503)
        """Return the CSRF token to embed in this session's mutating forms.

        An empty string means the adapter does not use CSRF protection (the
        dev/test doubles), so the template renders no meaningful token.
        """
        return ""

    # Async is required by the authentication port contract.
    async def check_csrf(  # NOSONAR(S7503)
        self,
        _request: Request,
        _submitted: str | None,
    ) -> bool:
        """Whether ``submitted`` matches the CSRF token bound to the session.

        The default (no-CSRF) adapters accept any request; adapters that keep a
        real session override this to reject a missing or mismatched token.
        """
        return True

    # Async is required by the authentication port contract.
    async def get_display_name(self, _request: Request) -> str:  # NOSONAR(S7503)
        """Return a human-readable name for the user, or "" if the adapter knows none."""
        return ""

    # Async is required by the authentication port contract.
    async def apply_pending_session_cookie(  # NOSONAR(S7503)
        self,
        _request: Request,
        _response: Response,
    ) -> None:
        """Write back a session cookie the request refreshed, if any.

        Called by :class:`~user_management_bff.session_middleware.SessionCookieMiddleware`
        once a response exists. Adapters that keep no cookie do nothing.
        """
        return None


class PermissionsPort(ABC):
    @abstractmethod
    async def get_permissions(self, actor: User, targets: list[Target]) -> dict[str, list[Permission]]:
        """
        This method returns the permissions the provided actor has on the given targets.
        """
