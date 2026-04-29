"""Utility helpers for computing and formatting env variable diffs."""

from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class DiffResult:
    """Structured result of comparing two env dictionaries."""

    added: Dict[str, str] = field(default_factory=dict)    # in right, not in left
    removed: Dict[str, str] = field(default_factory=dict)  # in left, not in right
    changed: Dict[str, Tuple[str, str]] = field(default_factory=dict)  # (left, right)

    @property
    def is_clean(self) -> bool:
        return not self.added and not self.removed and not self.changed

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.removed) + len(self.changed)


def compute_diff(left: Dict[str, str], right: Dict[str, str]) -> DiffResult:
    """Return a DiffResult comparing *left* (local) to *right* (vault)."""
    left_keys = set(left)
    right_keys = set(right)

    added = {k: right[k] for k in right_keys - left_keys}
    removed = {k: left[k] for k in left_keys - right_keys}
    changed = {
        k: (left[k], right[k])
        for k in left_keys & right_keys
        if left[k] != right[k]
    }
    return DiffResult(added=added, removed=removed, changed=changed)


def format_diff(result: DiffResult, *, mask_values: bool = False) -> str:
    """Return a human-readable string representation of a DiffResult."""
    if result.is_clean:
        return "No differences."

    lines = []

    def _val(v: str) -> str:
        return "***" if mask_values else v

    if result.added:
        lines.append("Added (in vault, not local):")
        for k in sorted(result.added):
            lines.append(f"  + {k}={_val(result.added[k])}")

    if result.removed:
        lines.append("Removed (in local, not vault):")
        for k in sorted(result.removed):
            lines.append(f"  - {k}={_val(result.removed[k])}")

    if result.changed:
        lines.append("Changed:")
        for k in sorted(result.changed):
            lv, rv = result.changed[k]
            lines.append(f"  ~ {k}: {_val(lv)} -> {_val(rv)}")

    return "\n".join(lines)
