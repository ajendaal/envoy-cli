"""Unit tests for envoy.profile (Profile dataclass and resolve_profile)."""

import pytest

from envoy.profile import Profile, ProfileError, resolve_profile


def test_valid_profile_creation():
    p = Profile(name="dev", variables={"DEBUG": "true"})
    assert p.name == "dev"
    assert p.variables == {"DEBUG": "true"}


def test_invalid_profile_name_raises():
    with pytest.raises(ProfileError, match="Invalid profile name"):
        Profile(name="123bad")


def test_profile_name_with_hyphens_and_underscores():
    p = Profile(name="prod-eu_west")
    assert p.name == "prod-eu_west"


def test_to_dict_and_from_dict_roundtrip():
    original = Profile(
        name="staging",
        variables={"API_URL": "https://staging.example.com"},
        description="Staging env",
        parent="base",
    )
    restored = Profile.from_dict(original.to_dict())
    assert restored.name == original.name
    assert restored.variables == original.variables
    assert restored.description == original.description
    assert restored.parent == original.parent


def test_resolve_profile_no_parent():
    p = Profile(name="dev", variables={"A": "1", "B": "2"})
    result = resolve_profile(p, {"dev": p})
    assert result == {"A": "1", "B": "2"}


def test_resolve_profile_inherits_parent():
    base = Profile(name="base", variables={"A": "base_a", "B": "base_b"})
    child = Profile(name="dev", variables={"B": "dev_b"}, parent="base")
    result = resolve_profile(child, {"base": base, "dev": child})
    assert result == {"A": "base_a", "B": "dev_b"}


def test_resolve_profile_missing_parent_raises():
    child = Profile(name="dev", variables={}, parent="nonexistent")
    with pytest.raises(ProfileError, match="unknown parent"):
        resolve_profile(child, {"dev": child})


def test_resolve_profile_circular_raises():
    a = Profile(name="a", variables={}, parent="b")
    b = Profile(name="b", variables={}, parent="a")
    with pytest.raises(ProfileError, match="Circular"):
        resolve_profile(a, {"a": a, "b": b})
