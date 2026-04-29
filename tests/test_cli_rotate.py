"""Tests for envoy.cli_rotate."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envoy.vault import Vault
from envoy.cli_rotate import rotate_group

PASS_OLD = "old-secret"
PASS_NEW = "new-secret"


@pytest.fixture()
def vault_dir(tmp_path):
    v = Vault(str(tmp_path), PASS_OLD)
    v.save("dev", {"FOO": "bar"})
    return str(tmp_path)


@pytest.fixture()
def runner():
    return CliRunner()


def _invoke(runner, vault_dir, extra_args=None, old=PASS_OLD, new=PASS_NEW):
    args = [
        "run",
        "--vault-dir", vault_dir,
        "--old-passphrase", old,
        "--new-passphrase", new,
    ]
    if extra_args:
        args.extend(extra_args)
    return runner.invoke(rotate_group, args, catch_exceptions=False)


def test_rotate_success_output(runner, vault_dir):
    result = _invoke(runner, vault_dir)
    assert result.exit_code == 0
    assert "rotated: dev" in result.output
    assert "1 profile(s)" in result.output


def test_rotate_updates_vault(runner, vault_dir):
    _invoke(runner, vault_dir)
    new_vault = Vault(vault_dir, PASS_NEW)
    assert new_vault.load("dev") == {"FOO": "bar"}


def test_rotate_single_profile_flag(runner, vault_dir):
    v = Vault(vault_dir, PASS_OLD)
    v.save("staging", {"X": "1"})
    result = _invoke(runner, vault_dir, extra_args=["--profile", "dev"])
    assert result.exit_code == 0
    assert "rotated: dev" in result.output
    assert "staging" not in result.output


def test_rotate_same_passphrase_error(runner, vault_dir):
    result = runner.invoke(
        rotate_group,
        [
            "run",
            "--vault-dir", vault_dir,
            "--old-passphrase", PASS_OLD,
            "--new-passphrase", PASS_OLD,
        ],
    )
    assert result.exit_code != 0
    assert "differ" in result.output


def test_rotate_wrong_passphrase_shows_error(runner, vault_dir):
    result = _invoke(runner, vault_dir, old="wrong")
    assert result.exit_code != 0


def test_rotate_empty_vault_no_profiles(runner, tmp_path):
    result = _invoke(runner, str(tmp_path))
    assert result.exit_code == 0
    assert "No profiles" in result.output
