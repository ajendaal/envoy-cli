"""CLI commands for diffing .env profiles against local files."""

import click
from pathlib import Path

from envoy.vault import Vault, VaultError
from envoy.env_parser import parse, diff, ParseError
from envoy.sync import pull


def _get_vault(vault_dir: str) -> Vault:
    return Vault(Path(vault_dir))


@click.group(name="diff")
def diff_group():
    """Compare local .env files with vault profiles."""


@diff_group.command(name="run")
@click.argument("profile")
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--passphrase", prompt=True, hide_input=True, help="Vault passphrase.")
@click.option("--vault-dir", default=".envoy", show_default=True)
def diff_cmd(profile: str, env_file: str, passphrase: str, vault_dir: str):
    """Show differences between a local ENV_FILE and a vault PROFILE."""
    vault = _get_vault(vault_dir)
    try:
        vault_data = pull(vault, profile, passphrase)
    except VaultError as exc:
        raise click.ClickException(str(exc))

    local_text = Path(env_file).read_text()
    try:
        local_data = parse(local_text)
    except ParseError as exc:
        raise click.ClickException(f"Failed to parse {env_file}: {exc}")

    added, removed, changed = diff(local_data, vault_data)

    if not added and not removed and not changed:
        click.echo("No differences found.")
        return

    if added:
        click.echo(click.style("Keys only in vault:", fg="green"))
        for key in sorted(added):
            click.echo(f"  + {key}={vault_data[key]}")

    if removed:
        click.echo(click.style("Keys only in local file:", fg="red"))
        for key in sorted(removed):
            click.echo(f"  - {key}={local_data[key]}")

    if changed:
        click.echo(click.style("Changed values:", fg="yellow"))
        for key in sorted(changed):
            click.echo(f"  ~ {key}: local={local_data[key]!r}  vault={vault_data[key]!r}")
