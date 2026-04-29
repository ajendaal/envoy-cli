"""Tests for envoy.rotate."""

from __future__ import annotations

import pytest

from envoy.vault import Vault
from envoy.rotate import rotate, RotateError


PASS_OLD = "old-secret"
PASS_NEW = "new-secret"

ENV_A = {"KEY1": "val1", "KEY2": "val2"}
ENV_B = {"ALPHA": "a", "BETA": "b"}


@pytest.fixture()
def vault_dir(tmp_path):
    v = Vault(str(tmp_path), PASS_OLD)
    v.save("dev", ENV_A)
    v.save("prod", ENV_B)
    return str(tmp_path)


def test_rotate_all_profiles(vault_dir):
    rotated = rotate(vault_dir, PASS_OLD, PASS_NEW)
    assert set(rotated) == {"dev", "prod"}


def test_rotated_data_readable_with_new_passphrase(vault_dir):
    rotate(vault_dir, PASS_OLD, PASS_NEW)
    new_vault = Vault(vault_dir, PASS_NEW)
    assert new_vault.load("dev") == ENV_A
    assert new_vault.load("prod") == ENV_B


def test_old_passphrase_rejected_after_rotation(vault_dir):
    rotate(vault_dir, PASS_OLD, PASS_NEW)
    old_vault = Vault(vault_dir, PASS_OLD)
    with pytest.raises(Exception):
        old_vault.load("dev")


def test_rotate_single_profile(vault_dir):
    rotated = rotate(vault_dir, PASS_OLD, PASS_NEW, profile="dev")
    assert rotated == ["dev"]
    # prod still encrypted under old passphrase
    old_vault = Vault(vault_dir, PASS_OLD)
    assert old_vault.load("prod") == ENV_B


def test_rotate_missing_profile_raises(vault_dir):
    with pytest.raises(RotateError, match="not found"):
        rotate(vault_dir, PASS_OLD, PASS_NEW, profile="staging")


def test_rotate_wrong_old_passphrase_raises(vault_dir):
    with pytest.raises(RotateError):
        rotate(vault_dir, "wrong-pass", PASS_NEW)


def test_rotate_empty_vault_returns_empty_list(tmp_path):
    rotated = rotate(str(tmp_path), PASS_OLD, PASS_NEW)
    assert rotated == []


def test_rotate_records_audit_entries(vault_dir):
    from envoy.audit import AuditLog

    rotate(vault_dir, PASS_OLD, PASS_NEW, actor="tester")
    log = AuditLog(vault_dir)
    entries = log.read()
    actions = [(e.profile, e.action, e.actor) for e in entries]
    assert ("dev", "rotate", "tester") in actions
    assert ("prod", "rotate", "tester") in actions
