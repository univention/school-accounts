# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from dataclasses import dataclass
from typing import Optional


@dataclass
class LoginCredentials:
    username: str
    password: str
    realm: str
    url: str
    user_realm: Optional[str] = None
    secure: bool = True


@dataclass
class ContextObject:
    login_credentials: Optional[LoginCredentials]
