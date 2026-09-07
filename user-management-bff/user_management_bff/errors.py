# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
from user_management_bff.lang import _


class BaseError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ObjectNotFoundError(BaseError):
    def __init__(self, identifier: str):
        super().__init__(_("Object not found"))
        self.identifier = identifier


class PermissionsError(BaseError): ...


class NoSchoolUserError(PermissionsError):
    def __init__(self, message: str, identifier: str):
        super().__init__(message)
        self.identifier = identifier


class NotAuthenticatedError(BaseError): ...


class PasswordChangeOnNextLoginUnsupportedError(BaseError):
    """The backend cannot force a password change at the next login for this user.

    Raised before the write, so the password is left unchanged: sending a password
    without the flag the actor asked for would silently do half the job.
    """

    def __init__(self, identifier: str):
        super().__init__("Password change at the next login is not available.")
        self.identifier: str = identifier


class PasswordResetRejectedError(BaseError):
    """The target system refused to change a user's password for this user.

    Distinct from PermissionsError: the actor is authorized to attempt the
    change (write-password already checked) - the target system rejects the
    value or the operation itself, e.g. a Kelvin/UDM password-policy
    violation. ``message`` is the target system's own rejection reason -
    the adapter raising this guarantees it's a plain string, but its content
    is otherwise unvetted (not translated, not length-bounded, not otherwise
    checked) and must never contain the password.
    """

    def __init__(self, identifier: str, message: str):
        super().__init__(message)
        self.identifier: str = identifier
