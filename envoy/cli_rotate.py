"""CLI commands for key rotation."""

from __future__ import annotations

import click

from .rotate import rotate, RotateError


@click.group("rotate", help="Re-encrypt vault entries under a new passphrase.")
def rotate_group() -> None:  # pragma: no cover
    pass


@rotate_group.command("run")
@click.option(
    "--vault-dir",
    default=".envoy",
    show_default=True,
    help="Path to the vault directory.",
)
@click.option(
    "--profile",
    default=None,
    help="Rotate only this profile (default: all profiles).",
)
@click.option(
    "--old-passphrase",
    prompt="Current passphrase",
    hide_input=True,
    help="Existing encryption passphrase.",
)
@click.option(
    "--new-passphrase",
    prompt="New passphrase",
    hide_input=True,
    confirmation_prompt=True,
    help="Replacement encryption passphrase.",
)
def run_cmd(
    vault_dir: str,
    profile: str | None,
    old_passphrase: str,
    new_passphrase: str,
) -> None:
    """Rotate the encryption key for vault entries."""
    if old_passphrase == new_passphrase:
        raise click.UsageError("New passphrase must differ from the current one.")
    try:
        rotated = rotate(
            vault_dir,
            old_passphrase=old_passphrase,
            new_passphrase=new_passphrase,
            profile=profile,
        )
    except RotateError as exc:
        raise click.ClickException(str(exc)) from exc

    if rotated:
        for name in rotated:
            click.echo(f"  rotated: {name}")
        click.echo(f"\nRotated {len(rotated)} profile(s) successfully.")
    else:
        click.echo("No profiles found to rotate.")
