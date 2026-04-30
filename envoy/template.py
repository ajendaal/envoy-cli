"""Template rendering: substitute .env values into template strings."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


class TemplateError(Exception):
    """Raised when template rendering fails."""


@dataclass
class RenderResult:
    output: str
    missing_keys: List[str]


def render(template: str, env: Dict[str, str], *, strict: bool = False) -> RenderResult:
    """Replace ``{{ KEY }}`` placeholders in *template* with values from *env*.

    Parameters
    ----------
    template:
        Raw template text containing ``{{ KEY }}`` placeholders.
    env:
        Mapping of environment variable names to values.
    strict:
        When *True*, raise :class:`TemplateError` if any placeholder has no
        corresponding key in *env*.  When *False* (default), leave the
        placeholder unchanged and record it in :attr:`RenderResult.missing_keys`.
    """
    missing: List[str] = []

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        key = match.group(1)
        if key in env:
            return env[key]
        missing.append(key)
        if strict:
            raise TemplateError(f"Missing key in env: '{key}'")
        return match.group(0)

    output = _PLACEHOLDER_RE.sub(_replace, template)
    return RenderResult(output=output, missing_keys=missing)


def list_placeholders(template: str) -> List[str]:
    """Return the unique placeholder keys found in *template*, in order of first appearance."""
    seen: dict[str, None] = {}
    for match in _PLACEHOLDER_RE.finditer(template):
        seen.setdefault(match.group(1), None)
    return list(seen)
