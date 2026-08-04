"""Static validation for generated Codex custom-agent TOML."""

from __future__ import annotations

from .model import VALID_REASONING_EFFORTS, ConfigError, Profile, validate_agent_name
from .validation_core import parse_toml, validate_managed_guardrails, validate_without_parser


def validate_agent_content(
    content: str,
    expected_name: str | None = None,
    expected_profile: Profile | None = None,
) -> list[str]:
    data = parse_toml(content)
    if data is None:
        return validate_without_parser(content, expected_name, expected_profile)

    messages: list[str] = []
    for required in ("name", "description", "developer_instructions"):
        value = data.get(required)
        if not isinstance(value, str) or not value.strip():
            raise ConfigError(f"Required custom-agent field `{required}` is missing or empty.")
    name = str(data["name"])
    validate_agent_name(name)
    if expected_name and name != expected_name:
        raise ConfigError(f"Agent name mismatch: expected {expected_name!r}, found {name!r}.")

    model = data.get("model")
    effort = data.get("model_reasoning_effort")
    tier = data.get("service_tier")
    if model is not None and not isinstance(model, str):
        raise ConfigError("`model` must be a string when present.")
    if effort is not None and (not isinstance(effort, str) or effort not in VALID_REASONING_EFFORTS):
        raise ConfigError(f"Unsupported `model_reasoning_effort`: {effort!r}.")
    if tier is not None and not isinstance(tier, str):
        raise ConfigError("`service_tier` must be a string when present.")
    features = data.get("features", {})
    if not isinstance(features, dict):
        raise ConfigError("`features` must be a TOML table when present.")
    fast_mode = features.get("fast_mode")
    if fast_mode is not None and not isinstance(fast_mode, bool):
        raise ConfigError("`features.fast_mode` must be a boolean when present.")
    if tier == "fast" and fast_mode is not True:
        raise ConfigError('`service_tier = "fast"` requires `[features].fast_mode = true`.')

    if expected_profile:
        actual = (model, effort, tier, bool(fast_mode))
        wanted = (
            expected_profile.model,
            expected_profile.reasoning_effort,
            expected_profile.service_tier,
            expected_profile.fast_mode,
        )
        if actual != wanted:
            raise ConfigError(f"Profile mismatch: expected {wanted!r}, found {actual!r}.")
        messages.append(f"Selected profile matched: {expected_profile.key}.")
    messages.extend(validate_managed_guardrails(content))
    messages.extend(
        [
            "Full TOML parse passed.",
            "Required custom-agent fields passed: name, description, developer_instructions.",
            f"Configured model: {model}.",
            f"Configured reasoning effort: {effort}.",
            f"Configured service tier: {tier or 'standard/default'}.",
        ]
    )
    return messages
