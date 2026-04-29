"""Utilities for parsing and serialising .env file content."""

import re
from typing import Optional

_COMMENT_RE = re.compile(r"^\s*#.*$")
_BLANK_RE = re.compile(r"^\s*$")
_PAIR_RE = re.compile(
    r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*="
    r"\s*(?P<q>['\"]?)(?P<val>.*?)(?P=q)\s*$"
)


class ParseError(ValueError):
    """Raised when a .env file line cannot be parsed."""


def parse(content: str, strict: bool = False) -> dict:
    """Parse .env file content into a dictionary.

    Args:
        content: Raw text content of a .env file.
        strict: If True, raise ParseError on malformed lines.

    Returns:
        Ordered dict of variable names to their string values.
    """
    result: dict = {}
    for lineno, line in enumerate(content.splitlines(), start=1):
        if _COMMENT_RE.match(line) or _BLANK_RE.match(line):
            continue
        match = _PAIR_RE.match(line)
        if not match:
            if strict:
                raise ParseError(f"Line {lineno}: cannot parse {line!r}")
            continue
        result[match.group(1)] = match.group("val")
    return result


def serialise(env_vars: dict, header: Optional[str] = None) -> str:
    """Serialise a dictionary back to .env file format.

    Args:
        env_vars: Mapping of variable names to values.
        header: Optional comment header prepended to the output.

    Returns:
        String in .env format.
    """
    lines = []
    if header:
        for h_line in header.splitlines():
            lines.append(f"# {h_line}" if not h_line.startswith("#") else h_line)
        lines.append("")
    for key, value in env_vars.items():
        if any(c in value for c in (" ", "\t", "'", '"', "$", "\\`")):
            escaped = value.replace('"', '\\"')
            lines.append(f'{key}="{escaped}"')
        else:
            lines.append(f"{key}={value}")
    return "\n".join(lines) + "\n"


def merge(base: dict, override: dict) -> dict:
    """Merge two env dicts; keys in override take precedence."""
    merged = dict(base)
    merged.update(override)
    return merged
