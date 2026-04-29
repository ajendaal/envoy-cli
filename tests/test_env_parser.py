"""Tests for envoy/env_parser.py — parse, serialise, merge, diff."""

import pytest

from envoy.env_parser import ParseError, parse, serialise, merge, diff


# ---------------------------------------------------------------------------
# parse()
# ---------------------------------------------------------------------------

class TestParse:
    def test_simple_key_value(self):
        result = parse("FOO=bar")
        assert result == {"FOO": "bar"}

    def test_multiple_pairs(self):
        text = "FOO=bar\nBAZ=qux\n"
        result = parse(text)
        assert result == {"FOO": "bar", "BAZ": "qux"}

    def test_double_quoted_value(self):
        result = parse('KEY="hello world"')
        assert result == {"KEY": "hello world"}

    def test_single_quoted_value(self):
        result = parse("KEY='hello world'")
        assert result == {"KEY": "hello world"}

    def test_empty_value(self):
        result = parse("KEY=")
        assert result == {"KEY": ""}

    def test_comment_lines_are_ignored(self):
        text = "# This is a comment\nFOO=bar"
        result = parse(text)
        assert result == {"FOO": "bar"}

    def test_blank_lines_are_ignored(self):
        text = "\nFOO=bar\n\nBAZ=qux\n"
        result = parse(text)
        assert result == {"FOO": "bar", "BAZ": "qux"}

    def test_inline_comment_stripped(self):
        # Values after an unquoted '#' should be treated as comments.
        result = parse("FOO=bar  # inline comment")
        assert result == {"FOO": "bar"}

    def test_inline_comment_inside_quotes_preserved(self):
        result = parse('FOO="bar # not a comment"')
        assert result == {"FOO": "bar # not a comment"}

    def test_invalid_line_raises(self):
        with pytest.raises(ParseError):
            parse("INVALID LINE WITHOUT EQUALS")

    def test_export_prefix_stripped(self):
        result = parse("export FOO=bar")
        assert result == {"FOO": "bar"}


# ---------------------------------------------------------------------------
# serialise()
# ---------------------------------------------------------------------------

class TestSerialise:
    def test_produces_key_equals_value_lines(self):
        env = {"FOO": "bar"}
        output = serialise(env)
        assert "FOO=bar" in output

    def test_values_with_spaces_are_quoted(self):
        env = {"KEY": "hello world"}
        output = serialise(env)
        assert 'KEY="hello world"' in output

    def test_roundtrip(self):
        env = {"FOO": "bar", "BAZ": "hello world", "EMPTY": ""}
        assert parse(serialise(env)) == env

    def test_keys_are_sorted(self):
        env = {"ZZZ": "1", "AAA": "2", "MMM": "3"}
        lines = [l for l in serialise(env).splitlines() if l]
        keys = [l.split("=")[0] for l in lines]
        assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# merge()
# ---------------------------------------------------------------------------

class TestMerge:
    def test_merge_combines_dicts(self):
        base = {"FOO": "1", "BAR": "2"}
        incoming = {"BAZ": "3"}
        result = merge(base, incoming)
        assert result == {"FOO": "1", "BAR": "2", "BAZ": "3"}

    def test_incoming_overwrites_base(self):
        base = {"FOO": "old"}
        incoming = {"FOO": "new"}
        result = merge(base, incoming)
        assert result["FOO"] == "new"

    def test_base_not_mutated(self):
        base = {"FOO": "1"}
        merge(base, {"FOO": "2"})
        assert base["FOO"] == "1"


# ---------------------------------------------------------------------------
# diff()
# ---------------------------------------------------------------------------

class TestDiff:
    def test_added_keys(self):
        old = {"FOO": "1"}
        new = {"FOO": "1", "BAR": "2"}
        result = diff(old, new)
        assert result["added"] == {"BAR": "2"}
        assert result["removed"] == {}
        assert result["changed"] == {}

    def test_removed_keys(self):
        old = {"FOO": "1", "BAR": "2"}
        new = {"FOO": "1"}
        result = diff(old, new)
        assert result["removed"] == {"BAR": "2"}
        assert result["added"] == {}

    def test_changed_keys(self):
        old = {"FOO": "old"}
        new = {"FOO": "new"}
        result = diff(old, new)
        assert result["changed"] == {"FOO": ("old", "new")}

    def test_identical_dicts_produce_empty_diff(self):
        env = {"FOO": "bar", "BAZ": "qux"}
        result = diff(env, env.copy())
        assert result == {"added": {}, "removed": {}, "changed": {}}
