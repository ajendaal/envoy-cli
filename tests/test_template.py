"""Tests for envoy.template."""
from __future__ import annotations

import pytest

from envoy.template import RenderResult, TemplateError, list_placeholders, render


ENV = {"HOST": "localhost", "PORT": "5432", "DB": "mydb"}


def test_render_simple_substitution():
    result = render("postgres://{{ HOST }}:{{ PORT }}/{{ DB }}", ENV)
    assert result.output == "postgres://localhost:5432/mydb"
    assert result.missing_keys == []


def test_render_with_whitespace_in_placeholder():
    result = render("{{  HOST  }} and {{ PORT}}", ENV)
    assert result.output == "localhost and 5432"


def test_render_missing_key_non_strict_leaves_placeholder():
    result = render("{{ HOST }}:{{ MISSING }}", ENV)
    assert "localhost" in result.output
    assert "{{ MISSING }}" in result.output
    assert result.missing_keys == ["MISSING"]


def test_render_missing_key_strict_raises():
    with pytest.raises(TemplateError, match="MISSING"):
        render("{{ MISSING }}", ENV, strict=True)


def test_render_no_placeholders():
    text = "no placeholders here"
    result = render(text, ENV)
    assert result.output == text
    assert result.missing_keys == []


def test_render_empty_env():
    result = render("{{ HOST }}", {})
    assert result.missing_keys == ["HOST"]
    assert result.output == "{{ HOST }}"


def test_render_result_is_dataclass():
    result = render("", {})
    assert isinstance(result, RenderResult)


def test_list_placeholders_returns_ordered_unique_keys():
    template = "{{ B }} {{ A }} {{ B }} {{ C }}"
    keys = list_placeholders(template)
    assert keys == ["B", "A", "C"]


def test_list_placeholders_empty_template():
    assert list_placeholders("no placeholders") == []


def test_list_placeholders_single_key():
    assert list_placeholders("Hello {{ NAME }}!") == ["NAME"]


def test_render_multiline_template():
    template = "HOST={{ HOST }}\nPORT={{ PORT }}\n"
    result = render(template, ENV)
    assert result.output == "HOST=localhost\nPORT=5432\n"
    assert result.missing_keys == []
