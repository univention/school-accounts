# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Annotated

import typer
from typer import Context, Option

from ..keycloak import KeycloakClientError, get_keycloak_client

app = typer.Typer()


@app.callback()
def realms_callback():
    """
    Commands to provision realms.
    """


@app.command()
def add(
    ctx: Context,
    realm_name: str,
    ignore_exists: Annotated[bool, Option(help="Ignore existing realms and exit successfully.")] = False,
):
    """
    Command to add a new realm.
    """
    try:
        client = get_keycloak_client(ctx.obj.login_credentials)
        client.create_realm(realm_name, ignore_exists=ignore_exists)
    except KeycloakClientError as exc:
        print(f"Realm creation failed with the following error: {exc.error_message}")
        raise typer.Exit(1)
