# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Annotated, Optional

import typer
from typer import Context, Option

from ..models import ContextObject, LoginCredentials
from .clients import app as clients_app
from .realms import app as realms_app
from .users import app as users_app

app = typer.Typer()
app.add_typer(realms_app, name="realms")
app.add_typer(users_app, name="users")
app.add_typer(clients_app, name="clients")


@app.callback()
def main_callback(
    ctx: Context,
    username: Annotated[str, Option(help="Username to authenticate with.")],
    password: Annotated[str, Option(help="Password to authenticate with.")],
    url: Annotated[str, Option(help="URL of the Keycloak server to login to.")],
    realm: Annotated[str, Option(help="Realm to login to")] = "ucs",
    user_realm: Annotated[
        Optional[str],
        Option(
            help="Realm of the user to authenticate with.\n" "Only required if it differs from realm."
        ),
    ] = None,
    secure: Annotated[
        bool, Option(help="Ignore SSL verification if False. Do not disable this option in production!")
    ] = True,
):
    """
    keycloak-provisioning allows you to provision your keycloak with new clients, users and realms.
    """
    ctx.obj = ContextObject(
        login_credentials=LoginCredentials(
            username=username,
            password=password,
            realm=realm,
            url=url,
            user_realm=user_realm,
            secure=secure,
        )
    )


def run_script():
    app()
