"""Tests for envoy.env_diff utility module."""

import pytest
from envoy.env_diff import DiffResult, compute_diff, format_diff


def test_clean_diff_on_identical_dicts():
    result = compute_diff({"A": "1", "B": "2"}, {"A": "1", "B": "2"})
    assert result.is_clean
    assert result.total_changes == 0


def test_added_keys_detected():
    result = compute_diff({"A": "1"}, {"A": "1", "B": "new"})
    assert "B" in result.added
    assert result.added["B"] == "new"
    assert not result.removed
    assert not result.changed


def test_removed_keys_detected():
    result = compute_diff({"A": "1", "B": "old"}, {"A": "1"})
    assert "B" in result.removed
    assert result.removed["B"] == "old"
    assert not result.added
    assert not result.changed


def test_changed_values_detected():
    result = compute_diff({"A": "old"}, {"A": "new"})
    assert "A" in result.changed
    assert result.changed["A"] == ("old", "new")
    assert not result.added
    assert not result.removed


def test_total_changes_counts_all_categories():
    result = compute_diff(
        {"A": "1", "B": "old", "C": "keep"},
        {"A": "1", "B": "new", "D": "added"},
    )
    # C removed, B changed, D added
    assert result.total_changes == 3


def test_format_diff_clean():
    result = DiffResult()
    assert format_diff(result) == "No differences."


def test_format_diff_shows_added():
    result = compute_diff({}, {"KEY": "val"})
    output = format_diff(result)
    assert "Added" in output
    assert "KEY=val" in output


def test_format_diff_shows_removed():
    result = compute_diff({"KEY": "val"}, {})
    output = format_diff(result)
    assert "Removed" in output
    assert "KEY=val" in output


def test_format_diff_shows_changed():
    result = compute_diff({"KEY": "old"}, {"KEY": "new"})
    output = format_diff(result)
    assert "Changed" in output
    assert "old" in output
    assert "new" in output


def test_format_diff_mask_values():
    result = compute_diff({"SECRET": "hunter2"}, {"SECRET": "pa$$word"})
    output = format_diff(result, mask_values=True)
    assert "hunter2" not in output
    assert "pa$$word" not in output
    assert "***" in output


def test_empty_dicts_are_clean():
    result = compute_diff({}, {})
    assert result.is_clean
