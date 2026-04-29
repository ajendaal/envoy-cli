"""Main CLI entry point for envoy."""
import click

from envoy.cli_profile import profile_group
from envoy.cli_sync import sync_group
from envoy.cli_audit import audit_group


@click.group()
@click.version_option(package_name="envoy-cli")
def main():
    """envoy — manage and sync .env files securely across environments."""


main.add_command(profile_group)
main.add_command(sync_group)
main.add_command(audit_group)

if __name__ == "__main__":
    main()
