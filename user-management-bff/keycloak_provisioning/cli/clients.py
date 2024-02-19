# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import json
from json import JSONDecodeError
from typing import Annotated, Optional

import typer
from rich import print
from typer import Argument, Context, FileText, Option

from ..keycloak import KeycloakClientError, get_keycloak_client

app = typer.Typer()


@app.callback()
def clients_callback():
    """
    Commands to provision clients.
    """


@app.command()
def add(
    ctx: Context,
    client_data: Annotated[FileText, Argument()],
    ignore_exists: Annotated[bool, Option(help="Ignore existing users and exit successfully.")] = False,
    override_secret: Annotated[
        Optional[str], Option(help="Override for the client secret value")
    ] = None,
    override_root_url: Annotated[Optional[str], Option(help="Override for the client root URL")] = None,
    override_redirect_urls: Annotated[
        Optional[list[str]], Option(help="Override for the client redirect URLs")
    ] = None,
    override_web_origins: Annotated[
        Optional[list[str]], Option(help="Override for the client web origins")
    ] = None,
):
    """
    Command to add a new client to a realm.
    """
    try:
        client_data = json.load(client_data)
    except JSONDecodeError:
        print("The provided client data is not a valid json file.")
        raise typer.Exit(1)
    overrides: dict = dict()
    if override_secret:
        overrides["secret"] = override_secret
    if override_root_url:
        overrides["rootUrl"] = override_root_url
    if override_redirect_urls:
        overrides["redirectUris"] = override_redirect_urls
    if override_web_origins:
        overrides["webOrigins"] = override_web_origins
    try:
        client = get_keycloak_client(ctx.obj.login_credentials)
        client.create_client({**client_data, **overrides}, ignore_exists=ignore_exists)
    except KeycloakClientError as exc:
        print(f"Client creation failed with the following error: {exc.error_message}")
        raise typer.Exit(1)
