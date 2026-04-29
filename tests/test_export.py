"""Tests for envoy.export."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envoy.vault import Vault
from envoy.export import export_env, ExportError

PASSPHRASE = "test-secret"
PROFILE = "staging"
ENV_CONTENT = "DB_HOST=localhost\nDB_PORT=5432\nSECRET=pa$$word\n"


@pytest.fixture()
def vault(tmp_path: Path) -> Vault:
    v = Vault(tmp_path / ".envoy")
    v.save(PASSPHRASE, PROFILE, ENV_CONTENT)
    return v


def test_export_dotenv_format(vault: Vault) -> None:
    result = export_env(vault, PASSPHRASE, PROFILE, fmt="dotenv")
    assert "DB_HOST=localhost" in result
    assert "DB_PORT=5432" in result


def test_export_json_format(vault: Vault) -> None:
    result = export_env(vault, PASSPHRASE, PROFILE, fmt="json")
    data = json.loads(result)
    assert data["DB_HOST"] == "localhost"
    assert data["DB_PORT"] == "5432"
    assert data["SECRET"] == "pa$$word"


def test_export_shell_format(vault: Vault) -> None:
    result = export_env(vault, PASSPHRASE, PROFILE, fmt="shell")
    assert 'export DB_HOST="localhost"' in result
    assert 'export SECRET="pa$$word"' in result


def test_export_shell_escapes_double_quotes(tmp_path: Path) -> None:
    v = Vault(tmp_path / ".envoy")
    v.save(PASSPHRASE, PROFILE, 'MSG=say "hello"\n')
    result = export_env(v, PASSPHRASE, PROFILE, fmt="shell")
    assert 'export MSG="say \\"hello\\""' in result


def test_export_writes_to_file(vault: Vault, tmp_path: Path) -> None:
    out = tmp_path / "staging.env"
    export_env(vault, PASSPHRASE, PROFILE, fmt="dotenv", output_path=out)
    assert out.exists()
    assert "DB_HOST=localhost" in out.read_text()


def test_export_unknown_format_raises(vault: Vault) -> None:
    with pytest.raises(ExportError, match="Unknown export format"):
        export_env(vault, PASSPHRASE, PROFILE, fmt="yaml")  # type: ignore[arg-type]


def test_export_missing_profile_raises(vault: Vault) -> None:
    with pytest.raises(ExportError, match="Could not load profile"):
        export_env(vault, PASSPHRASE, "nonexistent", fmt="dotenv")


def test_export_wrong_passphrase_raises(vault: Vault) -> None:
    with pytest.raises(ExportError, match="Could not load profile"):
        export_env(vault, "wrong-passphrase", PROFILE, fmt="dotenv")
