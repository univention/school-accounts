# SPDX-FileCopyrightText: 2024-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import json
import secrets
from json import JSONDecodeError
from pathlib import Path
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
    overrides: dict[str, str] = {}
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
    secret_file: Annotated[
        Path | None,
        Option(
            help="File holding the client secret; makes the client confidential.",
            exists=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
):
    """
    Command to modify a client
    """
    client_secret = secret_file.read_text().strip() if secret_file else None
    if secret_file and not client_secret:
        print(f"The secret file {secret_file} is empty.")
        raise typer.Exit(1)
    try:
        client = get_keycloak_client(ctx.obj.login_credentials)
        client.modify_client(
            client_id,
            append_redirect_urls=append_redirect_urls,
            remove_redirect_urls=remove_redirect_urls,
            client_secret=client_secret,
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
    Command to get a client secret. Prints nothing if the client has none.
    """
    try:
        client = get_keycloak_client(ctx.obj.login_credentials)
        client_secret = client.get_client_secret(client_id)
    except KeycloakClientError as exc:
        print(f"Getting client secret failed with the following error: {exc.error_message}")
        raise typer.Exit(1)
    if client_secret:
        typer.echo(client_secret)
