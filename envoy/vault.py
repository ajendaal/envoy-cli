"""Vault module for storing and retrieving encrypted .env files."""

import json
import os
from pathlib import Path
from typing import Optional

from envoy.crypto import decrypt, encrypt

DEFAULT_VAULT_DIR = Path.home() / ".envoy" / "vaults"


class VaultError(Exception):
    """Raised when a vault operation fails."""


class Vault:
    """Manages encrypted storage of .env file contents."""

    def __init__(self, name: str, vault_dir: Optional[Path] = None):
        self.name = name
        self.vault_dir = Path(vault_dir) if vault_dir else DEFAULT_VAULT_DIR
        self.vault_path = self.vault_dir / f"{name}.vault"

    def _ensure_vault_dir(self) -> None:
        self.vault_dir.mkdir(parents=True, exist_ok=True)

    def exists(self) -> bool:
        """Return True if the vault file exists on disk."""
        return self.vault_path.exists()

    def save(self, env_vars: dict, passphrase: str) -> None:
        """Encrypt and persist env_vars to the vault file."""
        self._ensure_vault_dir()
        plaintext = json.dumps(env_vars)
        ciphertext = encrypt(plaintext, passphrase)
        self.vault_path.write_text(ciphertext, encoding="utf-8")

    def load(self, passphrase: str) -> dict:
        """Decrypt and return env_vars from the vault file."""
        if not self.exists():
            raise VaultError(f"Vault '{self.name}' not found at {self.vault_path}")
        ciphertext = self.vault_path.read_text(encoding="utf-8")
        try:
            plaintext = decrypt(ciphertext, passphrase)
        except Exception as exc:
            raise VaultError(f"Failed to decrypt vault '{self.name}': {exc}") from exc
        return json.loads(plaintext)

    def delete(self) -> None:
        """Remove the vault file from disk."""
        if not self.exists():
            raise VaultError(f"Vault '{self.name}' does not exist.")
        self.vault_path.unlink()

    def list_keys(self, passphrase: str) -> list:
        """Return the list of variable names stored in the vault."""
        return list(self.load(passphrase).keys())


def list_vaults(vault_dir: Optional[Path] = None) -> list:
    """Return names of all vaults in the given directory."""
    directory = Path(vault_dir) if vault_dir else DEFAULT_VAULT_DIR
    if not directory.exists():
        return []
    return [p.stem for p in sorted(directory.glob("*.vault"))]
