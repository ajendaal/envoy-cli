"""Export .env files from the vault in various formats."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Literal

from envoy.vault import Vault, VaultError
from envoy.env_parser import parse, serialise

ExportFormat = Literal["dotenv", "json", "shell"]


class ExportError(Exception):
    """Raised when an export operation fails."""


def _to_shell(env_vars: Dict[str, str]) -> str:
    """Render env vars as export statements for shell sourcing."""
    lines = []
    for key, value in env_vars.items():
        escaped = value.replace('"', '\\"')
        lines.append(f'export {key}="{escaped}"')
    return "\n".join(lines) + ("\n" if lines else "")


def export_env(
    vault: Vault,
    passphrase: str,
    profile: str,
    fmt: ExportFormat = "dotenv",
    output_path: Path | None = None,
) -> str:
    """Export env vars for *profile* from *vault* in the requested format.

    Returns the rendered string and optionally writes it to *output_path*.
    Raises ExportError if the profile does not exist in the vault.
    """
    try:
        raw = vault.load(passphrase, profile)
    except VaultError as exc:
        raise ExportError(f"Could not load profile '{profile}': {exc}") from exc

    env_vars = parse(raw)

    if fmt == "dotenv":
        rendered = serialise(env_vars)
    elif fmt == "json":
        rendered = json.dumps(env_vars, indent=2) + "\n"
    elif fmt == "shell":
        rendered = _to_shell(env_vars)
    else:
        raise ExportError(f"Unknown export format: {fmt!r}")

    if output_path is not None:
        output_path.write_text(rendered, encoding="utf-8")

    return rendered
