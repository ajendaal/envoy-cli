"""Sync .env variables between local files and the vault."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from envoy.env_parser import parse, serialise, merge, diff, ParseError
from envoy.vault import Vault, VaultError
from envoy.profile_store import ProfileStore


class SyncError(Exception):
    """Raised when a sync operation fails."""


def push(
    env_path: Path,
    vault: Vault,
    passphrase: str,
    profile_name: str = "default",
    overwrite: bool = False,
) -> dict[str, str]:
    """Read a local .env file and push its variables into the vault.

    Returns the merged mapping that was saved.
    """
    try:
        local_vars = parse(env_path.read_text())
    except (OSError, ParseError) as exc:
        raise SyncError(f"Cannot read local env file: {exc}") from exc

    existing: dict[str, str] = {}
    if vault.exists(profile_name):
        try:
            existing = vault.load(profile_name, passphrase)
        except VaultError as exc:
            raise SyncError(f"Cannot load vault profile '{profile_name}': {exc}") from exc

    merged = merge(existing, local_vars) if not overwrite else {**existing, **local_vars}
    try:
        vault.save(profile_name, merged, passphrase)
    except VaultError as exc:
        raise SyncError(f"Cannot save to vault: {exc}") from exc

    return merged


def pull(
    env_path: Path,
    vault: Vault,
    passphrase: str,
    profile_name: str = "default",
    overwrite: bool = False,
) -> dict[str, str]:
    """Pull variables from the vault and write them to a local .env file.

    Returns the mapping written to disk.
    """
    if not vault.exists(profile_name):
        raise SyncError(f"Profile '{profile_name}' does not exist in the vault.")

    try:
        vault_vars = vault.load(profile_name, passphrase)
    except VaultError as exc:
        raise SyncError(f"Cannot load vault profile '{profile_name}': {exc}") from exc

    local_vars: dict[str, str] = {}
    if env_path.exists() and not overwrite:
        try:
            local_vars = parse(env_path.read_text())
        except ParseError as exc:
            raise SyncError(f"Cannot parse existing env file: {exc}") from exc

    final = merge(local_vars, vault_vars) if not overwrite else vault_vars

    try:
        env_path.write_text(serialise(final))
    except OSError as exc:
        raise SyncError(f"Cannot write env file: {exc}") from exc

    return final


def status(
    env_path: Path,
    vault: Vault,
    passphrase: str,
    profile_name: str = "default",
) -> list[tuple[str, str]]:
    """Return the diff between local .env and the vault for a given profile.

    Each entry is (key, change) where change is one of 'added', 'removed', 'changed'.
    """
    local_vars: dict[str, str] = {}
    if env_path.exists():
        try:
            local_vars = parse(env_path.read_text())
        except ParseError as exc:
            raise SyncError(f"Cannot parse env file: {exc}") from exc

    vault_vars: dict[str, str] = {}
    if vault.exists(profile_name):
        try:
            vault_vars = vault.load(profile_name, passphrase)
        except VaultError as exc:
            raise SyncError(f"Cannot load vault profile '{profile_name}': {exc}") from exc

    return diff(vault_vars, local_vars)
