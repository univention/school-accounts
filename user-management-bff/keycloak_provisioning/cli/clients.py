# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

import json
import secrets
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
    ignore_exists: Annotated[bool, Option(help="Ignore existing client and exit successfully.")] = False,
    create_secret: Annotated[bool, Option(help="Create client secret.")] = False,
    home_url: Annotated[Optional[str], Option(help="Override for the client home URL")] = None,
):
    """
    Command to add a new client to a realm.
    """
    try:
        client_json = json.load(client_data)
    except JSONDecodeError:
        print("The provided client data is not a valid json file.")
        raise typer.Exit(1)
    overrides: dict = dict()
    if create_secret:
        overrides["secret"] = secrets.token_urlsafe(24)
    if home_url:
        overrides["baseUrl"] = home_url
    try:
        client = get_keycloak_client(ctx.obj.login_credentials)
        client.create_client({**client_json, **overrides}, ignore_exists=ignore_exists)
    except KeycloakClientError as exc:
        print(f"Client creation failed with the following error: {exc.error_message}")
        raise typer.Exit(1)


@app.command()
def modify(
    ctx: Context,
    client_id: Annotated[str, Argument()],
    append_redirect_urls: Annotated[
        Optional[list[str]], Option(help="Append client redirect URLs")
    ] = None,
    remove_redirect_urls: Annotated[
        Optional[list[str]], Option(help="Remove client redirect URLs")
    ] = None,
):
    """
    Command to modify a client
    """
    try:
        client = get_keycloak_client(ctx.obj.login_credentials)
        client.modify_client(
            client_id,
            append_redirect_urls=append_redirect_urls,
            remove_redirect_urls=remove_redirect_urls,
        )
    except KeycloakClientError as exc:
        print(f"Client modification failed with the following error: {exc.error_message}")
        raise typer.Exit(1)


@app.command()
def get_secret(
    ctx: Context,
    client_id: Annotated[str, Argument()],
):
    """
    Command to get a client secret
    """
    try:
        client = get_keycloak_client(ctx.obj.login_credentials)
        print(client.get_client_secret(client_id))
    except KeycloakClientError as exc:
        print(f"Getting client secret failed with the following error: {exc.error_message}")
        raise typer.Exit(1)
