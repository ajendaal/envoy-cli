"""CLI commands for profile management (plug into a Click group)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import click

from envoy.profile import Profile, ProfileError, resolve_profile
from envoy.profile_store import ProfileStore

_DEFAULT_VAULT = Path.home() / ".envoy" / "vault"


def _get_store(vault_dir: Path, passphrase: str) -> ProfileStore:
    return ProfileStore(vault_dir, passphrase)


@click.group(name="profile")
@click.option("--vault", default=str(_DEFAULT_VAULT), show_default=True, help="Vault directory.")
@click.option("--passphrase", envvar="ENVOY_PASSPHRASE", prompt=True, hide_input=True)
@click.pass_context
def profile_group(ctx: click.Context, vault: str, passphrase: str) -> None:
    """Manage named environment profiles."""
    ctx.ensure_object(dict)
    ctx.obj["store"] = _get_store(Path(vault), passphrase)


@profile_group.command("list")
@click.pass_context
def list_profiles(ctx: click.Context) -> None:
    """List all profiles."""
    store: ProfileStore = ctx.obj["store"]
    names = store.list_profiles()
    if not names:
        click.echo("No profiles found.")
    else:
        for name in names:
            click.echo(name)


@profile_group.command("set")
@click.argument("profile_name")
@click.argument("key_value_pairs", nargs=-1, metavar="KEY=VALUE ...")
@click.option("--parent", default=None, help="Inherit from this profile.")
@click.option("--description", default="", help="Human-readable description.")
@click.pass_context
def set_profile(ctx, profile_name, key_value_pairs, parent, description):
    """Create or update a profile with KEY=VALUE pairs."""
    store: ProfileStore = ctx.obj["store"]
    variables = {}
    for pair in key_value_pairs:
        if "=" not in pair:
            raise click.BadParameter(f"Expected KEY=VALUE, got {pair!r}")
        k, v = pair.split("=", 1)
        variables[k.strip()] = v.strip()
    try:
        p = Profile(name=profile_name, variables=variables, description=description, parent=parent or None)
        store.save(p)
        click.echo(f"Profile {profile_name!r} saved.")
    except ProfileError as exc:
        raise click.ClickException(str(exc)) from exc


@profile_group.command("show")
@click.argument("profile_name")
@click.option("--resolve", is_flag=True, help="Resolve inheritance chain.")
@click.pass_context
def show_profile(ctx, profile_name, resolve):
    """Show variables for a profile."""
    store: ProfileStore = ctx.obj["store"]
    try:
        profile = store.get(profile_name)
        if resolve:
            variables = resolve_profile(profile, store.all_profiles())
        else:
            variables = profile.variables
        for k, v in sorted(variables.items()):
            click.echo(f"{k}={v}")
    except ProfileError as exc:
        raise click.ClickException(str(exc)) from exc


@profile_group.command("delete")
@click.argument("profile_name")
@click.confirmation_option(prompt="Are you sure you want to delete this profile?")
@click.pass_context
def delete_profile(ctx, profile_name):
    """Delete a profile."""
    store: ProfileStore = ctx.obj["store"]
    try:
        store.delete(profile_name)
        click.echo(f"Profile {profile_name!r} deleted.")
    except ProfileError as exc:
        raise click.ClickException(str(exc)) from exc
