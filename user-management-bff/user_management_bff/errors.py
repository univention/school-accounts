# Copyright (C) 2024 Univention GmbH
#
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
