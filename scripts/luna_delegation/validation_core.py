"""Shared TOML parsing and fallback checks for Luna agent validation."""

from __future__ import annotations

import re
from typing import Any, Mapping

from .model import (
    MANAGED_HEADER,
    REQUIRED_MANAGED_GUARDRAILS,
    ConfigError,
    Profile,
    toml_basic_string,
)

try:  # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:  # pragma: no cover
        tomllib = None  # type: ignore[assignment]


def parse_toml(content: str) -> Mapping[str, Any] | None:
    if tomllib is None:
        return None
    try:
        parsed = tomllib.loads(content)
    except Exception as exc:
        raise ConfigError(f"TOML parse failed: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ConfigError("TOML root must be a table/object.")
    return parsed


def validate_managed_guardrails(content: str) -> list[str]:
    if MANAGED_HEADER not in content:
        return []
    missing = [marker for marker in REQUIRED_MANAGED_GUARDRAILS if marker not in content]
    if missing:
        raise ConfigError(
            "Managed delegation guardrails are incomplete; missing: " + ", ".join(missing)
        )
    return ["Managed delegation contract and surface guardrails passed."]


def validate_without_parser(
    content: str,
    expected_name: str | None,
    expected_profile: Profile | None,
) -> list[str]:
    messages: list[str] = []
    patterns = {
        "name": r'(?m)^name\s*=\s*".+"\s*$',
        "description": r'(?m)^description\s*=\s*".+"\s*$',
        "developer_instructions": r'(?m)^developer_instructions\s*=\s*"""',
    }
    missing = [key for key, pattern in patterns.items() if not re.search(pattern, content)]
    if missing:
        raise ConfigError(f"Structural validation failed; missing: {', '.join(missing)}")
    if expected_name:
        pattern = rf'(?m)^name\s*=\s*{re.escape(toml_basic_string(expected_name))}\s*$'
        if not re.search(pattern, content):
            raise ConfigError(f"Agent name does not match expected value: {expected_name!r}.")
    if expected_profile:
        pairs = {
            "model": expected_profile.model,
            "model_reasoning_effort": expected_profile.reasoning_effort,
        }
        if expected_profile.service_tier:
            pairs["service_tier"] = expected_profile.service_tier
        for key, value in pairs.items():
            pattern = rf'(?m)^{re.escape(key)}\s*=\s*{re.escape(toml_basic_string(value))}\s*$'
            if not re.search(pattern, content):
                raise ConfigError(f"Profile mismatch: expected `{key} = {toml_basic_string(value)}`.")
        has_tier = re.search(r"(?m)^service_tier\s*=", content) is not None
        has_fast = re.search(r"(?m)^fast_mode\s*=\s*true\s*$", content) is not None
        if expected_profile.service_tier is None and has_tier:
            raise ConfigError(f"Profile {expected_profile.key!r} expects no explicit service_tier.")
        if has_fast is not expected_profile.fast_mode:
            raise ConfigError(f"Profile {expected_profile.key!r} has the wrong fast_mode setting.")
        messages.append(f"Selected profile matched: {expected_profile.key}.")
    messages.extend(validate_managed_guardrails(content))
    messages.append("Structural validation passed; install Python 3.11+ or tomli for full TOML parsing.")
    return messages
