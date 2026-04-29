"""Persist and retrieve profiles inside the encrypted vault."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from envoy.profile import Profile, ProfileError
from envoy.vault import Vault, VaultError

_PROFILES_KEY = "__profiles__"


class ProfileStore:
    """Stores named profiles as a special entry inside a Vault."""

    def __init__(self, vault_dir: Path, passphrase: str) -> None:
        self._vault = Vault(vault_dir, passphrase)
        self._passphrase = passphrase

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_all_raw(self) -> Dict[str, dict]:
        if not self._vault.exists(_PROFILES_KEY):
            return {}
        raw = self._vault.load(_PROFILES_KEY)
        return json.loads(raw)

    def _save_all_raw(self, data: Dict[str, dict]) -> None:
        self._vault.save(_PROFILES_KEY, json.dumps(data))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_profiles(self) -> List[str]:
        """Return sorted list of profile names."""
        return sorted(self._load_all_raw().keys())

    def get(self, name: str) -> Profile:
        raw = self._load_all_raw()
        if name not in raw:
            raise ProfileError(f"Profile {name!r} does not exist.")
        return Profile.from_dict(raw[name])

    def save(self, profile: Profile) -> None:
        raw = self._load_all_raw()
        raw[profile.name] = profile.to_dict()
        self._save_all_raw(raw)

    def delete(self, name: str) -> None:
        raw = self._load_all_raw()
        if name not in raw:
            raise ProfileError(f"Profile {name!r} does not exist.")
        # Check no other profile inherits from this one
        dependents = [
            p["name"] for p in raw.values() if p.get("parent") == name
        ]
        if dependents:
            raise ProfileError(
                f"Cannot delete {name!r}: profiles {dependents} inherit from it."
            )
        del raw[name]
        self._save_all_raw(raw)

    def all_profiles(self) -> Dict[str, Profile]:
        return {k: Profile.from_dict(v) for k, v in self._load_all_raw().items()}
