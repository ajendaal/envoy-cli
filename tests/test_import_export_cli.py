"""Tests for the env import/export CLI commands."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envoy.vault import Vault
from envoy.sync import push
from envoy.import_export_cli import env_group


@pytest.fixture()
def vault_dir(tmp_path):
    return tmp_path / ".envoy"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def populated_vault(vault_dir, tmp_path):
    """A vault with a 'dev' profile already pushed."""
    env_file = tmp_path / ".env"
    env_file.write_text("KEY1=hello\nKEY2=world\n")
    vault = Vault(vault_dir)
    push(vault, "secret", "dev", env_file)
    return vault_dir


def test_export_dotenv_format(runner, populated_vault):
    result = runner.invoke(
        env_group,
        ["export", "dev", "--vault-dir", str(populated_vault), "--passphrase", "secret"],
    )
    assert result.exit_code == 0
    assert "KEY1=hello" in result.output
    assert "KEY2=world" in result.output


def test_export_json_format(runner, populated_vault):
    result = runner.invoke(
        env_group,
        ["export", "dev", "--vault-dir", str(populated_vault),
         "--passphrase", "secret", "--format", "json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["KEY1"] == "hello"


def test_export_to_file(runner, populated_vault, tmp_path):
    out = tmp_path / "out.env"
    result = runner.invoke(
        env_group,
        ["export", "dev", "--vault-dir", str(populated_vault),
         "--passphrase", "secret", "--output", str(out)],
    )
    assert result.exit_code == 0
    assert out.exists()
    assert "KEY1=hello" in out.read_text()


def test_export_wrong_passphrase(runner, populated_vault):
    result = runner.invoke(
        env_group,
        ["export", "dev", "--vault-dir", str(populated_vault), "--passphrase", "wrong"],
    )
    assert result.exit_code != 0


def test_import_creates_profile(runner, vault_dir, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\nBAZ=qux\n")
    result = runner.invoke(
        env_group,
        ["import", "staging", str(env_file),
         "--vault-dir", str(vault_dir), "--passphrase", "secret"],
    )
    assert result.exit_code == 0
    assert "2 added" in result.output


def test_import_overwrite_flag(runner, vault_dir, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=original\n")
    runner.invoke(
        env_group,
        ["import", "prod", str(env_file),
         "--vault-dir", str(vault_dir), "--passphrase", "secret"],
    )
    env_file.write_text("FOO=updated\n")
    result = runner.invoke(
        env_group,
        ["import", "prod", str(env_file),
         "--vault-dir", str(vault_dir), "--passphrase", "secret", "--overwrite"],
    )
    assert result.exit_code == 0
    assert "1 updated" in result.output
