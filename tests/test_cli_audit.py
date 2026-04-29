"""Tests for envoy.cli_audit CLI commands."""
from pathlib import Path

import pytest
from click.testing import CliRunner

from envoy.audit import AuditLog, AUDIT_FILE
from envoy.cli_audit import audit_group


@pytest.fixture
def vault_dir(tmp_path: Path) -> Path:
    d = tmp_path / ".envoy"
    d.mkdir()
    return d


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_log_empty(runner: CliRunner, vault_dir: Path):
    result = runner.invoke(audit_group, ["log", "--vault-dir", str(vault_dir)])
    assert result.exit_code == 0
    assert "No audit entries found" in result.output


def test_log_shows_entries(runner: CliRunner, vault_dir: Path):
    log = AuditLog(vault_dir / AUDIT_FILE)
    log.record("push", "production", details="5 keys")
    log.record("pull", "staging")

    result = runner.invoke(audit_group, ["log", "--vault-dir", str(vault_dir)])
    assert result.exit_code == 0
    assert "push" in result.output
    assert "production" in result.output
    assert "pull" in result.output
    assert "staging" in result.output


def test_log_filters_by_profile(runner: CliRunner, vault_dir: Path):
    log = AuditLog(vault_dir / AUDIT_FILE)
    log.record("push", "production")
    log.record("push", "staging")

    result = runner.invoke(
        audit_group, ["log", "--vault-dir", str(vault_dir), "--profile", "staging"]
    )
    assert result.exit_code == 0
    assert "staging" in result.output
    assert "production" not in result.output


def test_clear_removes_log(runner: CliRunner, vault_dir: Path):
    log = AuditLog(vault_dir / AUDIT_FILE)
    log.record("push", "dev")

    result = runner.invoke(audit_group, ["clear", "--vault-dir", str(vault_dir), "--yes"])
    assert result.exit_code == 0
    assert not (vault_dir / AUDIT_FILE).exists()


def test_log_limit(runner: CliRunner, vault_dir: Path):
    log = AuditLog(vault_dir / AUDIT_FILE)
    for i in range(10):
        log.record("push", f"profile-{i}")

    result = runner.invoke(
        audit_group, ["log", "--vault-dir", str(vault_dir), "--limit", "3"]
    )
    assert result.exit_code == 0
    lines = [l for l in result.output.splitlines() if "profile-" in l]
    assert len(lines) == 3
