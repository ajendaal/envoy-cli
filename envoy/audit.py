"""Audit log for tracking vault and sync operations."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

AUDIT_FILE = ".envoy_audit.jsonl"


@dataclass
class AuditEntry:
    action: str
    profile: str
    user: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "profile": self.profile,
            "user": self.user,
            "timestamp": self.timestamp,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        return cls(
            action=data["action"],
            profile=data["profile"],
            user=data["user"],
            timestamp=data["timestamp"],
            details=data.get("details"),
        )


class AuditLog:
    def __init__(self, path: Path):
        self._path = path

    def record(self, action: str, profile: str, details: Optional[str] = None) -> AuditEntry:
        user = os.environ.get("ENVOY_USER") or os.environ.get("USER") or "unknown"
        entry = AuditEntry(action=action, profile=profile, user=user, details=details)
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry.to_dict()) + "\n")
        return entry

    def read(self, profile: Optional[str] = None, limit: int = 50) -> List[AuditEntry]:
        if not self._path.exists():
            return []
        entries: List[AuditEntry] = []
        with self._path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = AuditEntry.from_dict(json.loads(line))
                except (json.JSONDecodeError, KeyError):
                    continue
                if profile is None or entry.profile == profile:
                    entries.append(entry)
        return entries[-limit:]

    def clear(self) -> None:
        if self._path.exists():
            self._path.unlink()
