"""CLI commands for the audit log."""
from __future__ import annotations

from pathlib import Path

import click

from envoy.audit import AuditLog, AUDIT_FILE


def _get_log(vault_dir: str) -> AuditLog:
    return AuditLog(Path(vault_dir) / AUDIT_FILE)


@click.group("audit")
def audit_group():
    """View and manage the operation audit log."""


@audit_group.command("log")
@click.option("--vault-dir", default=".envoy", show_default=True, help="Vault directory.")
@click.option("--profile", default=None, help="Filter by profile name.")
@click.option("--limit", default=20, show_default=True, help="Maximum entries to show.")
def show_log(vault_dir: str, profile: str | None, limit: int):
    """Display recent audit log entries."""
    log = _get_log(vault_dir)
    entries = log.read(profile=profile, limit=limit)
    if not entries:
        click.echo("No audit entries found.")
        return
    click.echo(f"{'TIMESTAMP':<30} {'USER':<15} {'PROFILE':<15} {'ACTION':<10} DETAILS")
    click.echo("-" * 85)
    for e in entries:
        details = e.details or ""
        click.echo(f"{e.timestamp:<30} {e.user:<15} {e.profile:<15} {e.action:<10} {details}")


@audit_group.command("clear")
@click.option("--vault-dir", default=".envoy", show_default=True, help="Vault directory.")
@click.confirmation_option(prompt="Are you sure you want to clear the audit log?")
def clear_log(vault_dir: str):
    """Clear all audit log entries."""
    log = _get_log(vault_dir)
    log.clear()
    click.echo("Audit log cleared.")
