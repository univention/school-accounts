# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
from typing import Optional

from user_management_bff.lang import _
from user_management_bff.models import Permission


class BaseError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class OperationNotSupportedError(BaseError): ...


class PersistenceError(BaseError): ...


class ObjectNotFoundError(PersistenceError):
    def __init__(self, identifier: str):
        super().__init__(_("Object not found"))
        self.identifier = identifier


class CreationError(PersistenceError):
    def __init__(self, message: str):
        super().__init__(message)


class PermissionsError(BaseError):
    def __init__(self, message: str, missing_permissions: Optional[list[Permission]] = None):
        super().__init__(message)
        self.missing_permissions = missing_permissions if missing_permissions else []


class NoSchoolUserError(PermissionsError):
    def __init__(self, message: str, identifier: str):
        super().__init__(message)
        self.identifier = identifier


class NotAuthenticatedError(BaseError): ...
