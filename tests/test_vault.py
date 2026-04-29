"""Tests for envoy.vault module."""

import json
import pytest
from pathlib import Path

from envoy.vault import Vault, VaultError, list_vaults

PASSPHRASE = "super-secret-passphrase"
SAMPLE_ENV = {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "abc123"}


@pytest.fixture
def tmp_vault(tmp_path):
    return Vault("test", vault_dir=tmp_path)


def test_vault_does_not_exist_initially(tmp_vault):
    assert not tmp_vault.exists()


def test_save_creates_vault_file(tmp_vault):
    tmp_vault.save(SAMPLE_ENV, PASSPHRASE)
    assert tmp_vault.exists()


def test_save_and_load_roundtrip(tmp_vault):
    tmp_vault.save(SAMPLE_ENV, PASSPHRASE)
    loaded = tmp_vault.load(PASSPHRASE)
    assert loaded == SAMPLE_ENV


def test_load_wrong_passphrase_raises(tmp_vault):
    tmp_vault.save(SAMPLE_ENV, PASSPHRASE)
    with pytest.raises(VaultError, match="Failed to decrypt"):
        tmp_vault.load("wrong-passphrase")


def test_load_nonexistent_vault_raises(tmp_vault):
    with pytest.raises(VaultError, match="not found"):
        tmp_vault.load(PASSPHRASE)


def test_delete_removes_vault_file(tmp_vault):
    tmp_vault.save(SAMPLE_ENV, PASSPHRASE)
    tmp_vault.delete()
    assert not tmp_vault.exists()


def test_delete_nonexistent_vault_raises(tmp_vault):
    with pytest.raises(VaultError, match="does not exist"):
        tmp_vault.delete()


def test_list_keys_returns_variable_names(tmp_vault):
    tmp_vault.save(SAMPLE_ENV, PASSPHRASE)
    keys = tmp_vault.list_keys(PASSPHRASE)
    assert set(keys) == set(SAMPLE_ENV.keys())


def test_list_vaults_returns_vault_names(tmp_path):
    for name in ("alpha", "beta", "gamma"):
        Vault(name, vault_dir=tmp_path).save(SAMPLE_ENV, PASSPHRASE)
    names = list_vaults(vault_dir=tmp_path)
    assert names == ["alpha", "beta", "gamma"]


def test_list_vaults_empty_directory(tmp_path):
    assert list_vaults(vault_dir=tmp_path) == []


def test_list_vaults_missing_directory(tmp_path):
    missing = tmp_path / "nonexistent"
    assert list_vaults(vault_dir=missing) == []
