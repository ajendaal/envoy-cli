"""Tests for the diff CLI commands."""

import pytest
from pathlib import Path
from click.testing import CliRunner

from envoy.vault import Vault
from envoy.sync import push
from envoy.diff_cli import diff_group


PASSPHRASE = "test-secret"


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path / ".envoy"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def populated_vault(vault_dir: Path) -> Path:
    vault = Vault(vault_dir)
    push(vault, "staging", PASSPHRASE, {"KEY1": "val1", "KEY2": "val2", "SHARED": "same"})
    return vault_dir


def _invoke(runner, vault_dir, env_file, profile="staging", passphrase=PASSPHRASE):
    return runner.invoke(
        diff_group,
        ["run", profile, str(env_file), "--passphrase", passphrase, "--vault-dir", str(vault_dir)],
    )


def test_no_differences(runner, populated_vault, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("KEY1=val1\nKEY2=val2\nSHARED=same\n")
    result = _invoke(runner, populated_vault, env_file)
    assert result.exit_code == 0
    assert "No differences found" in result.output


def test_shows_added_keys(runner, populated_vault, tmp_path):
    """Keys in vault but not in local file appear as added."""
    env_file = tmp_path / ".env"
    env_file.write_text("KEY1=val1\nSHARED=same\n")
    result = _invoke(runner, populated_vault, env_file)
    assert result.exit_code == 0
    assert "Keys only in vault" in result.output
    assert "KEY2" in result.output


def test_shows_removed_keys(runner, populated_vault, tmp_path):
    """Keys in local file but not in vault appear as removed."""
    env_file = tmp_path / ".env"
    env_file.write_text("KEY1=val1\nKEY2=val2\nSHARED=same\nLOCAL_ONLY=foo\n")
    result = _invoke(runner, populated_vault, env_file)
    assert result.exit_code == 0
    assert "Keys only in local file" in result.output
    assert "LOCAL_ONLY" in result.output


def test_shows_changed_values(runner, populated_vault, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("KEY1=different\nKEY2=val2\nSHARED=same\n")
    result = _invoke(runner, populated_vault, env_file)
    assert result.exit_code == 0
    assert "Changed values" in result.output
    assert "KEY1" in result.output


def test_wrong_passphrase_shows_error(runner, populated_vault, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("KEY1=val1\n")
    result = _invoke(runner, populated_vault, env_file, passphrase="wrong")
    assert result.exit_code != 0
    assert "Error" in result.output


def test_missing_profile_shows_error(runner, populated_vault, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("KEY1=val1\n")
    result = _invoke(runner, populated_vault, env_file, profile="nonexistent")
    assert result.exit_code != 0
