"""CLI commands for rendering env templates."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from envoy.template import TemplateError, list_placeholders, render
from envoy.vault import Vault


def _get_vault(vault_dir: str) -> Vault:
    return Vault(Path(vault_dir))


@click.group(name="template")
def template_group() -> None:
    """Render files using .env values from the vault."""


@template_group.command(name="render")
@click.argument("template_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--profile", "-p", required=True, help="Profile whose env values to use.")
@click.option("--passphrase", prompt=True, hide_input=True, help="Vault passphrase.")
@click.option("--output", "-o", default="-", help="Output file path (default: stdout).")
@click.option("--strict", is_flag=True, default=False, help="Fail on missing placeholders.")
@click.option("--vault-dir", default=".envoy", show_default=True, envvar="ENVOY_VAULT_DIR")
def render_cmd(
    template_file: str,
    profile: str,
    passphrase: str,
    output: str,
    strict: bool,
    vault_dir: str,
) -> None:
    """Render TEMPLATE_FILE substituting {{ KEY }} with env values."""
    vault = _get_vault(vault_dir)
    try:
        env = vault.load(profile, passphrase)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    template_text = Path(template_file).read_text(encoding="utf-8")
    try:
        result = render(template_text, env, strict=strict)
    except TemplateError as exc:
        raise click.ClickException(str(exc)) from exc

    if result.missing_keys:
        click.echo(
            f"Warning: {len(result.missing_keys)} placeholder(s) not resolved: "
            + ", ".join(result.missing_keys),
            err=True,
        )

    if output == "-":
        click.echo(result.output, nl=False)
    else:
        Path(output).write_text(result.output, encoding="utf-8")
        click.echo(f"Rendered output written to {output}")


@template_group.command(name="inspect")
@click.argument("template_file", type=click.Path(exists=True, dir_okay=False))
def inspect_cmd(template_file: str) -> None:
    """List all {{ KEY }} placeholders found in TEMPLATE_FILE."""
    template_text = Path(template_file).read_text(encoding="utf-8")
    keys = list_placeholders(template_text)
    if not keys:
        click.echo("No placeholders found.")
        return
    for key in keys:
        click.echo(key)
