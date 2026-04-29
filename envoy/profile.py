"""Profile management: named environment sets (e.g. dev, staging, prod)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

PROFILE_NAME_RE = re.compile(r'^[a-zA-Z][a-zA-Z0-9_-]{0,63}$')


class ProfileError(Exception):
    """Raised for profile-related errors."""


@dataclass
class Profile:
    """A named collection of environment variable overrides."""

    name: str
    variables: Dict[str, str] = field(default_factory=dict)
    description: str = ""
    parent: Optional[str] = None  # inherit from another profile

    def __post_init__(self) -> None:
        if not PROFILE_NAME_RE.match(self.name):
            raise ProfileError(
                f"Invalid profile name {self.name!r}. "
                "Must start with a letter and contain only letters, digits, hyphens, or underscores."
            )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parent": self.parent,
            "variables": self.variables,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        return cls(
            name=data["name"],
            variables=data.get("variables", {}),
            description=data.get("description", ""),
            parent=data.get("parent"),
        )


def resolve_profile(
    profile: Profile,
    all_profiles: Dict[str, Profile],
    _seen: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Return merged variables, honouring parent inheritance (child wins)."""
    if _seen is None:
        _seen = []
    if profile.name in _seen:
        raise ProfileError(
            f"Circular profile inheritance detected: {' -> '.join(_seen + [profile.name])}"
        )
    _seen = _seen + [profile.name]

    base: Dict[str, str] = {}
    if profile.parent:
        if profile.parent not in all_profiles:
            raise ProfileError(
                f"Profile {profile.name!r} references unknown parent {profile.parent!r}."
            )
        base = resolve_profile(all_profiles[profile.parent], all_profiles, _seen)

    return {**base, **profile.variables}
