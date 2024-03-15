# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only


class BaseError(Exception):
    def __init__(self, message: str):  # pragma: no cover
        super().__init__(message)
        self.message = message


class OperationNotSupportedError(BaseError): ...


class PersistenceError(BaseError): ...


class ObjectNotFoundError(PersistenceError):
    def __init__(self, identifier: str):  # pragma: no cover
        super().__init__("Object not found: {}".format(identifier))
        self.identifier = identifier


class CreationError(PersistenceError):
    def __init__(self, message: str):  # pragma: no cover
        super().__init__(message)


class PermissionsError(BaseError): ...


class NoSchoolUserError(PermissionsError):
    def __init__(self, message: str, identifier: str):
        super().__init__(message)
        self.identifier = identifier
