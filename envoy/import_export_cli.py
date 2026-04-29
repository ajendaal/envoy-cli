"""CLI commands for importing and exporting .env files."""

import click
from pathlib import Path

from envoy.vault import Vault, VaultError
from envoy.export import export_env, ExportError
from envoy.sync import push, SyncError
from envoy.audit import AuditLog


def _get_vault(vault_dir: str) -> Vault:
    return Vault(Path(vault_dir))


@click.group(name="env")
def env_group():
    """Import and export .env files."""


@env_group.command(name="export")
@click.argument("profile")
@click.option("--vault-dir", default=".envoy", show_default=True)
@click.option("--passphrase", prompt=True, hide_input=True)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["dotenv", "json", "shell"]),
    default="dotenv",
    show_default=True,
)
@click.option("--output", "-o", type=click.Path(), default=None,
              help="Write output to file instead of stdout.")
def export_cmd(profile: str, vault_dir: str, passphrase: str, fmt: str, output: str):
    """Export a profile's env vars to stdout or a file."""
    vault = _get_vault(vault_dir)
    try:
        result = export_env(vault, passphrase, profile, fmt)
    except (VaultError, ExportError) as exc:
        raise click.ClickException(str(exc))

    if output:
        Path(output).write_text(result)
        click.echo(f"Exported '{profile}' ({fmt}) → {output}")
    else:
        click.echo(result, nl=False)


@env_group.command(name="import")
@click.argument("profile")
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--vault-dir", default=".envoy", show_default=True)
@click.option("--passphrase", prompt=True, hide_input=True)
@click.option("--overwrite", is_flag=True, default=False,
              help="Replace existing keys instead of merging.")
def import_cmd(profile: str, env_file: str, vault_dir: str, passphrase: str, overwrite: bool):
    """Import an .env file into the vault under PROFILE."""
    vault = _get_vault(vault_dir)
    log = AuditLog(Path(vault_dir))
    env_path = Path(env_file)
    try:
        added, updated = push(
            vault, passphrase, profile, env_path,
            overwrite=overwrite,
        )
        log.record(profile, "import", {"added": added, "updated": updated, "source": env_file})
    except (VaultError, SyncError) as exc:
        raise click.ClickException(str(exc))

    click.echo(f"Imported '{env_file}' into profile '{profile}': {added} added, {updated} updated.")
