"""Key rotation: re-encrypt vault entries under a new passphrase."""

from __future__ import annotations

from typing import Optional

from .vault import Vault, VaultError
from .audit import AuditLog


class RotateError(Exception):
    """Raised when key rotation fails."""


def rotate(
    vault_dir: str,
    old_passphrase: str,
    new_passphrase: str,
    profile: Optional[str] = None,
    actor: str = "cli",
) -> list[str]:
    """Re-encrypt vault entries from *old_passphrase* to *new_passphrase*.

    If *profile* is given only that profile's entry is rotated; otherwise
    every entry in the vault is rotated.

    Returns the list of profile names that were rotated.
    """
    vault = Vault(vault_dir, old_passphrase)
    log = AuditLog(vault_dir)

    try:
        profiles = vault.list_profiles()
    except VaultError as exc:
        raise RotateError(f"Cannot list vault profiles: {exc}") from exc

    if profile is not None:
        if profile not in profiles:
            raise RotateError(f"Profile '{profile}' not found in vault.")
        profiles = [profile]

    if not profiles:
        return []

    # Load all entries with the old passphrase first so we fail early.
    entries: dict[str, dict[str, str]] = {}
    for name in profiles:
        try:
            entries[name] = vault.load(name)
        except VaultError as exc:
            raise RotateError(
                f"Failed to decrypt profile '{name}' with old passphrase: {exc}"
            ) from exc

    # Re-save under the new passphrase.
    new_vault = Vault(vault_dir, new_passphrase)
    for name, env in entries.items():
        try:
            new_vault.save(name, env)
        except VaultError as exc:
            raise RotateError(
                f"Failed to re-encrypt profile '{name}': {exc}"
            ) from exc
        log.record(name, "rotate", actor=actor)

    return list(entries.keys())
