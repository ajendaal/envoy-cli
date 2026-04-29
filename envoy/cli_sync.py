"""CLI commands for syncing .env files with the vault."""
from __future__ import annotations

from pathlib import Path

import click

from envoy.vault import Vault
from envoy.sync import push, pull, status, SyncError

_DEFAULT_ENV = ".env"
_DEFAULT_VAULT = ".envoy/vault"


def _get_vault(vault_dir: str) -> Vault:
    return Vault(Path(vault_dir))


@click.group(name="sync")
def sync_group() -> None:
    """Sync .env files with the encrypted vault."""


@sync_group.command("push")
@click.option("--env", "env_path", default=_DEFAULT_ENV, show_default=True, help="Path to local .env file.")
@click.option("--vault", "vault_dir", default=_DEFAULT_VAULT, show_default=True, help="Vault directory.")
@click.option("--profile", default="default", show_default=True, help="Vault profile name.")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite vault values with local values.")
@click.password_option("--passphrase", prompt="Vault passphrase", help="Encryption passphrase.")
def push_cmd(env_path: str, vault_dir: str, profile: str, overwrite: bool, passphrase: str) -> None:
    """Push local .env variables into the vault."""
    vault = _get_vault(vault_dir)
    try:
        merged = push(Path(env_path), vault, passphrase, profile, overwrite)
    except SyncError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(click.style(f"Pushed {len(merged)} variable(s) to profile '{profile}'.", fg="green"))


@sync_group.command("pull")
@click.option("--env", "env_path", default=_DEFAULT_ENV, show_default=True, help="Path to local .env file.")
@click.option("--vault", "vault_dir", default=_DEFAULT_VAULT, show_default=True, help="Vault directory.")
@click.option("--profile", default="default", show_default=True, help="Vault profile name.")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite local values with vault values.")
@click.option("--passphrase", prompt="Vault passphrase", hide_input=True, help="Encryption passphrase.")
def pull_cmd(env_path: str, vault_dir: str, profile: str, overwrite: bool, passphrase: str) -> None:
    """Pull vault variables into a local .env file."""
    vault = _get_vault(vault_dir)
    try:
        final = pull(Path(env_path), vault, passphrase, profile, overwrite)
    except SyncError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(click.style(f"Pulled {len(final)} variable(s) into '{env_path}'.", fg="green"))


@sync_group.command("status")
@click.option("--env", "env_path", default=_DEFAULT_ENV, show_default=True, help="Path to local .env file.")
@click.option("--vault", "vault_dir", default=_DEFAULT_VAULT, show_default=True, help="Vault directory.")
@click.option("--profile", default="default", show_default=True, help="Vault profile name.")
@click.option("--passphrase", prompt="Vault passphrase", hide_input=True, help="Encryption passphrase.")
def status_cmd(env_path: str, vault_dir: str, profile: str, passphrase: str) -> None:
    """Show diff between local .env and the vault."""
    vault = _get_vault(vault_dir)
    try:
        changes = status(Path(env_path), vault, passphrase, profile)
    except SyncError as exc:
        raise click.ClickException(str(exc)) from exc

    if not changes:
        click.echo("No differences found — local and vault are in sync.")
        return

    colours = {"added": "green", "removed": "red", "changed": "yellow"}
    for key, change in changes:
        click.echo(click.style(f"  {change.upper():8s} {key}", fg=colours.get(change, "white")))
