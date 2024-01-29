# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from enum import StrEnum, auto

from pydantic import BaseModel


class SortingChoice(StrEnum):
    ASC = auto()
    DESC = auto()


class FormatterChoice(StrEnum):
    STRING = auto()
    LIST = auto()


class ColumnConfig(BaseModel):
    label: str
    attribute: str
    order: int
    sorting: SortingChoice = SortingChoice.ASC
    formatter: FormatterChoice = FormatterChoice.STRING


class ListUsersConfig(BaseModel):
    columns: list[ColumnConfig]
