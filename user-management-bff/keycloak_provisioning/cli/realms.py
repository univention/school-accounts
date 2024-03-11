# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import json
from json import JSONDecodeError
from typing import Annotated, Optional

import typer
from typer import Context, FileText, Option

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
    realm_data: Annotated[
        Optional[FileText], Option(help="Additional data with which to set up the realm")
    ] = None,
    ignore_exists: Annotated[bool, Option(help="Ignore existing realms and exit successfully.")] = False,
):
    """
    Command to add a new realm.
    """
    if realm_data:
        try:
            realm_json = json.load(realm_data)
        except JSONDecodeError:
            print("The provided realm data is not a valid json file.")
            raise typer.Exit(1)
    else:
        realm_json = {}

    try:
        client = get_keycloak_client(ctx.obj.login_credentials)
        client.create_realm(realm_name, ignore_exists=ignore_exists, realm_data=realm_json)
    except KeycloakClientError as exc:
        print(f"Realm creation failed with the following error: {exc.error_message}")
        raise typer.Exit(1)
