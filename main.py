#!/bin/env python
"""The main entry point for the ultimate pollbot."""
from contextlib import contextmanager

import typer

from pollbot.config import config
from pollbot.db import engine, base
from pollbot.models import *  # noqa
from pollbot.pollbot import updater

cli = typer.Typer()


@contextmanager
def wrap_echo(msg: str):
    typer.echo(f"{msg}... ", nl=False)
    yield
    typer.echo("done.")


@cli.command()
def initdb():
    """Set up the database.

    Can be used to remove an existing database.
    """
    typer.echo(f"Using database at {engine.url}")

    with engine.connect() as con:
        with wrap_echo("Installing pgcrypto extension"):
            con.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
            pass

    with wrap_echo("Creating metadata"):
        base.metadata.create_all()
        pass

    typer.echo("Database initialization complete.")


@cli.command()
def run():
    """Actually start the bot."""
    if config["webhook"]["enabled"]:
        typer.echo("Starting the bot in webhook mode.")
        domain = config["webhook"]["domain"]
        token = config["webhook"]["token"]
        updater.start_webhook(
            listen="127.0.0.1",
            port=config["webhook"]["port"],
            url_path=config["webhook"]["token"],
            webhook_url=f"{domain}{token}",
            cert=config["webhook"]["cert_path"],
        )
    else:
        typer.echo("Starting the bot in polling mode.")
        updater.start_polling()
        updater.idle()


if __name__ == "__main__":
    cli()
