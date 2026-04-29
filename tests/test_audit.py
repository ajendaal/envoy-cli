"""Tests for envoy.audit module."""
import json
from pathlib import Path

import pytest

from envoy.audit import AuditEntry, AuditLog


@pytest.fixture
def log(tmp_path: Path) -> AuditLog:
    return AuditLog(tmp_path / "audit.jsonl")


def test_record_creates_file(log: AuditLog, tmp_path: Path):
    log.record("push", "production")
    assert (tmp_path / "audit.jsonl").exists()


def test_record_returns_entry(log: AuditLog):
    entry = log.record("pull", "staging", details="3 keys synced")
    assert entry.action == "pull"
    assert entry.profile == "staging"
    assert entry.details == "3 keys synced"
    assert entry.timestamp  # non-empty ISO string


def test_read_returns_recorded_entries(log: AuditLog):
    log.record("push", "dev")
    log.record("pull", "dev")
    entries = log.read()
    assert len(entries) == 2
    assert entries[0].action == "push"
    assert entries[1].action == "pull"


def test_read_filters_by_profile(log: AuditLog):
    log.record("push", "dev")
    log.record("push", "production")
    log.record("pull", "dev")
    entries = log.read(profile="dev")
    assert len(entries) == 2
    assert all(e.profile == "dev" for e in entries)


def test_read_respects_limit(log: AuditLog):
    for i in range(10):
        log.record("push", "dev")
    entries = log.read(limit=5)
    assert len(entries) == 5


def test_read_empty_log(log: AuditLog):
    assert log.read() == []


def test_clear_removes_file(log: AuditLog, tmp_path: Path):
    log.record("push", "dev")
    log.clear()
    assert not (tmp_path / "audit.jsonl").exists()


def test_clear_on_nonexistent_file_is_safe(log: AuditLog):
    log.clear()  # should not raise


def test_audit_entry_roundtrip():
    entry = AuditEntry(action="push", profile="prod", user="alice", details="ok")
    restored = AuditEntry.from_dict(entry.to_dict())
    assert restored.action == entry.action
    assert restored.profile == entry.profile
    assert restored.user == entry.user
    assert restored.details == entry.details
