"""Integration tests for ProfileStore (uses a real temp vault directory)."""

import pytest

from envoy.profile import Profile, ProfileError
from envoy.profile_store import ProfileStore


@pytest.fixture
def store(tmp_path):
    return ProfileStore(tmp_path / "vault", passphrase="s3cr3t")


def test_empty_store_has_no_profiles(store):
    assert store.list_profiles() == []


def test_save_and_list(store):
    store.save(Profile(name="dev", variables={"DEBUG": "1"}))
    store.save(Profile(name="prod", variables={"DEBUG": "0"}))
    assert store.list_profiles() == ["dev", "prod"]


def test_get_existing_profile(store):
    store.save(Profile(name="dev", variables={"X": "42"}))
    p = store.get("dev")
    assert p.name == "dev"
    assert p.variables["X"] == "42"


def test_get_missing_profile_raises(store):
    with pytest.raises(ProfileError, match="does not exist"):
        store.get("ghost")


def test_overwrite_existing_profile(store):
    store.save(Profile(name="dev", variables={"A": "old"}))
    store.save(Profile(name="dev", variables={"A": "new"}))
    assert store.get("dev").variables["A"] == "new"


def test_delete_profile(store):
    store.save(Profile(name="dev", variables={}))
    store.delete("dev")
    assert "dev" not in store.list_profiles()


def test_delete_missing_profile_raises(store):
    with pytest.raises(ProfileError, match="does not exist"):
        store.delete("ghost")


def test_delete_profile_with_dependents_raises(store):
    store.save(Profile(name="base", variables={}))
    store.save(Profile(name="dev", variables={}, parent="base"))
    with pytest.raises(ProfileError, match="inherit from it"):
        store.delete("base")


def test_all_profiles_returns_dict(store):
    store.save(Profile(name="dev", variables={"K": "v"}))
    profiles = store.all_profiles()
    assert "dev" in profiles
    assert isinstance(profiles["dev"], Profile)


def test_wrong_passphrase_cannot_read(tmp_path):
    writer = ProfileStore(tmp_path / "vault", passphrase="correct")
    writer.save(Profile(name="dev", variables={"SECRET": "yes"}))

    reader = ProfileStore(tmp_path / "vault", passphrase="wrong")
    from envoy.vault import VaultError
    with pytest.raises((VaultError, Exception)):
        reader.list_profiles()
