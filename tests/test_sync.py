"""Tests for envoy.sync (push / pull / status)."""
from __future__ import annotations

from pathlib import Path

import pytest

from envoy.vault import Vault
from envoy.sync import push, pull, status, SyncError

PASSPHRASE = "test-secret"


@pytest.fixture()
def vault(tmp_path: Path) -> Vault:
    return Vault(tmp_path / "vault")


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("FOO=bar\nBAZ=qux\n")
    return p


# ---------------------------------------------------------------------------
# push
# ---------------------------------------------------------------------------

def test_push_creates_vault_entry(vault: Vault, env_file: Path) -> None:
    merged = push(env_file, vault, PASSPHRASE)
    assert vault.exists("default")
    assert merged["FOO"] == "bar"
    assert merged["BAZ"] == "qux"


def test_push_merges_with_existing(vault: Vault, env_file: Path) -> None:
    vault.save("default", {"EXISTING": "value"}, PASSPHRASE)
    push(env_file, vault, PASSPHRASE)
    loaded = vault.load("default", PASSPHRASE)
    assert loaded["EXISTING"] == "value"
    assert loaded["FOO"] == "bar"


def test_push_overwrite_replaces_vault_keys(vault: Vault, env_file: Path) -> None:
    vault.save("default", {"FOO": "old", "ONLY_VAULT": "keep"}, PASSPHRASE)
    push(env_file, vault, PASSPHRASE, overwrite=True)
    loaded = vault.load("default", PASSPHRASE)
    assert loaded["FOO"] == "bar"
    assert loaded["ONLY_VAULT"] == "keep"


def test_push_missing_env_file_raises(vault: Vault, tmp_path: Path) -> None:
    with pytest.raises(SyncError, match="Cannot read local env file"):
        push(tmp_path / "missing.env", vault, PASSPHRASE)


# ---------------------------------------------------------------------------
# pull
# ---------------------------------------------------------------------------

def test_pull_writes_env_file(vault: Vault, tmp_path: Path) -> None:
    vault.save("default", {"KEY": "val"}, PASSPHRASE)
    out = tmp_path / ".env"
    final = pull(out, vault, PASSPHRASE)
    assert out.exists()
    assert final["KEY"] == "val"
    assert "KEY=val" in out.read_text()


def test_pull_merges_with_local(vault: Vault, env_file: Path) -> None:
    vault.save("default", {"NEW": "from-vault"}, PASSPHRASE)
    pull(env_file, vault, PASSPHRASE)
    text = env_file.read_text()
    assert "FOO=bar" in text
    assert "NEW=from-vault" in text


def test_pull_missing_profile_raises(vault: Vault, tmp_path: Path) -> None:
    with pytest.raises(SyncError, match="does not exist in the vault"):
        pull(tmp_path / ".env", vault, PASSPHRASE, profile_name="ghost")


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------

def test_status_no_diff_when_in_sync(vault: Vault, env_file: Path) -> None:
    push(env_file, vault, PASSPHRASE)
    changes = status(env_file, vault, PASSPHRASE)
    assert changes == []


def test_status_detects_added_key(vault: Vault, env_file: Path) -> None:
    push(env_file, vault, PASSPHRASE)
    env_file.write_text("FOO=bar\nBAZ=qux\nNEW=extra\n")
    changes = status(env_file, vault, PASSPHRASE)
    keys = {k for k, _ in changes}
    assert "NEW" in keys


def test_status_empty_local_shows_all_removed(vault: Vault, tmp_path: Path) -> None:
    vault.save("default", {"A": "1", "B": "2"}, PASSPHRASE)
    empty = tmp_path / ".env"
    empty.write_text("")
    changes = status(empty, vault, PASSPHRASE)
    assert len(changes) == 2
