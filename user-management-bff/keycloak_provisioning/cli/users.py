# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Annotated

import typer
from typer import Argument, Context, Option

from ..keycloak import KeycloakClientError, get_keycloak_client

app = typer.Typer()


@app.callback()
def users_callback():
    """
    Commands to provision users.
    """


@app.command()
def add(
    ctx: Context,
    username: Annotated[str, Argument(help="Username for the new user.")],
    password: Annotated[str, Argument(help="Password for the new user.")],
    ignore_exists: Annotated[bool, Option(help="Ignore existing users and exit successfully.")] = False,
):
    """
    Command to add a new user to a realm.

    Do not use this command in a productive UCS environment. Here users are provisioned by LDAP.
    """
    try:
        client = get_keycloak_client(ctx.obj.login_credentials)
        client.create_user(username, password, ignore_exists=ignore_exists)
    except KeycloakClientError as exc:
        print(f"User creation failed with the following error: {exc.error_message}")
        raise typer.Exit(1)
