"""Entry point for the envoy CLI."""

import click

from envoy.cli_profile import profile_group
from envoy.cli_sync import sync_group
from envoy.cli_audit import audit_group
from envoy.import_export_cli import env_group


@click.group()
@click.version_option(package_name="envoy-cli")
def main():
    """envoy — manage and sync .env files securely."""


main.add_command(profile_group)
main.add_command(sync_group)
main.add_command(audit_group)
main.add_command(env_group)
