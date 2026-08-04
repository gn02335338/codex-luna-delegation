from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "configure_luna_agent.py"
SPEC = importlib.util.spec_from_file_location("configure_luna_agent", SCRIPT)
if SPEC is None or SPEC.loader is None:  # pragma: no cover
    raise RuntimeError(f"Unable to load {SCRIPT}")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ConfigureLunaAgentTests(unittest.TestCase):
    def test_all_generated_profiles_validate(self) -> None:
        for profile_key, profile in MODULE.PROFILES.items():
            with self.subTest(profile=profile_key):
                name = MODULE.DEFAULT_AGENT_NAME_BY_PROFILE[profile_key]
                content = MODULE.build_agent_toml(name, profile)
                messages = MODULE.validate_agent_content(
                    content, expected_name=name, expected_profile=profile
                )
                self.assertTrue(any("guardrails" in message for message in messages))

    def test_exact_profile_enables_fast_mode(self) -> None:
        content = MODULE.build_agent_toml("luna-max-fast", MODULE.PROFILES["exact"])
        self.assertIn('model = "gpt-5.6-luna"', content)
        self.assertIn('model_reasoning_effort = "max"', content)
        self.assertIn('service_tier = "fast"', content)
        self.assertIn("fast_mode = true", content)

    def test_economy_profile_omits_fast_settings(self) -> None:
        content = MODULE.build_agent_toml("luna-economy", MODULE.PROFILES["economy"])
        self.assertNotIn("service_tier", content)
        self.assertNotIn("fast_mode", content)
        self.assertIn('model_reasoning_effort = "medium"', content)

    def test_generated_agent_contains_surface_and_completion_guardrails(self) -> None:
        content = MODULE.build_agent_toml("luna-economy", MODULE.PROFILES["economy"])
        for marker in MODULE.REQUIRED_MANAGED_GUARDRAILS:
            with self.subTest(marker=marker):
                self.assertIn(marker, content)
        self.assertIn("Do not copy secrets", content)
        self.assertIn("Do not spawn additional agents", content)

    def test_contract_contains_required_sections(self) -> None:
        contract = MODULE.build_delegation_contract("luna-economy")
        required = (
            "Why delegation is justified",
            "Source-of-truth inputs",
            "Success predicate",
            "Does not count",
            "Editable",
            "Locked/read-only",
            "Append-only",
            "Human-controlled",
            "Acceptance evidence",
            "Return condition",
            "Stop conditions",
        )
        for section in required:
            with self.subTest(section=section):
                self.assertIn(section, contract)

    def test_routing_block_has_net_benefit_and_verification_rules(self) -> None:
        block = MODULE.build_routing_block("luna-economy")
        self.assertIn("context-isolation", block)
        self.assertIn("materially improves", block)
        self.assertIn("independently re-check", block)
        self.assertIn("total coordinator + worker + verification usage", block)

    def test_upsert_preserves_unrelated_content_and_replaces_managed_block(self) -> None:
        old = (
            "# Existing guidance\n\n"
            f"{MODULE.ROUTING_START}\nold managed content\n{MODULE.ROUTING_END}\n\n"
            "# Keep this footer\n"
        )
        new_block = MODULE.build_routing_block("luna-economy")
        updated = MODULE.upsert_marked_block(old, new_block)
        self.assertIn("# Existing guidance", updated)
        self.assertIn("# Keep this footer", updated)
        self.assertNotIn("old managed content", updated)
        self.assertEqual(updated.count(MODULE.ROUTING_START), 1)
        self.assertEqual(updated.count(MODULE.ROUTING_END), 1)

    def test_unpaired_routing_marker_is_rejected(self) -> None:
        with self.assertRaises(MODULE.ConfigError):
            MODULE.upsert_marked_block(MODULE.ROUTING_START, MODULE.build_routing_block("luna"))


if __name__ == "__main__":
    unittest.main()
