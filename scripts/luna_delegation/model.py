"""Profiles and generated Sol/Luna delegation artifacts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping

MANAGED_HEADER = "# Managed by codex-luna-delegation."
ROUTING_START = "<!-- codex-luna-delegation:start -->"
ROUTING_END = "<!-- codex-luna-delegation:end -->"
DEFAULT_AGENT_NAME_BY_PROFILE = {
    "exact": "luna-max-fast",
    "economy": "luna-economy",
    "fast-balanced": "luna-fast",
}
VALID_REASONING_EFFORTS = {"none", "low", "medium", "high", "xhigh", "max", "ultra"}
NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
REQUIRED_MANAGED_GUARDRAILS = (
    "Success predicate",
    "Does not count",
    "Editable",
    "Locked/read-only",
    "Append-only",
    "Human-controlled",
    "Acceptance evidence",
    "Return COMPLETE only",
)


@dataclass(frozen=True)
class Profile:
    key: str
    model: str
    reasoning_effort: str
    service_tier: str | None
    fast_mode: bool
    purpose: str


PROFILES: Mapping[str, Profile] = {
    "exact": Profile(
        key="exact",
        model="gpt-5.6-luna",
        reasoning_effort="max",
        service_tier="fast",
        fast_mode=True,
        purpose=(
            "Matches the requested Luna Max + Fast combination; quality/speed first, "
            "not minimum-credit mode."
        ),
    ),
    "economy": Profile(
        key="economy",
        model="gpt-5.6-luna",
        reasoning_effort="medium",
        service_tier=None,
        fast_mode=False,
        purpose="Recommended when the main goal is lower usage for clear, bounded work.",
    ),
    "fast-balanced": Profile(
        key="fast-balanced",
        model="gpt-5.6-luna",
        reasoning_effort="medium",
        service_tier="fast",
        fast_mode=True,
        purpose="Faster bounded execution without maximum reasoning on routine work.",
    ),
}


class ConfigError(RuntimeError):
    """Raised for safe, user-actionable configuration errors."""


def validate_agent_name(name: str) -> None:
    if not NAME_PATTERN.fullmatch(name):
        raise ConfigError(
            "Agent name must be 1-64 characters, begin with a letter or digit, "
            "and contain only letters, digits, hyphens, or underscores."
        )


def toml_basic_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def build_agent_toml(agent_name: str, profile: Profile) -> str:
    description = (
        "Execution-focused GPT-5.6 Luna subagent for one narrow, independent unit with a success "
        "predicate, classified surfaces, explicit output, and acceptance evidence. Use when context "
        "isolation or parallelism materially helps bounded implementation, tests, extraction, review, "
        "or investigation. Do not use for planning, architecture, scope changes, approvals, deployment, "
        "destructive actions, or ambiguous work."
    )
    instructions = f"""You are {agent_name}, an execution-focused subagent.

Mission and authority:
- Provide context isolation for exactly one bounded delegated unit. Do not create work merely to simulate a team.
- The parent agent retains the overall goal, architecture, planning, cross-task decisions, integration, permissions, and final acceptance.
- Execute only the delegated objective. Treat the parent contract as fixed unless it contains a direct contradiction.
- Do not spawn additional agents.

Required delegation contract:
- Objective: one bounded outcome.
- Source-of-truth inputs: exact files, refs, commands, data, versions, and freshness.
- Success predicate: every condition that must be true before completion.
- Does not count: plausible near misses, narrowed scope, partial artifacts, or unsupported claims.
- Surfaces: Editable, Locked/read-only, Append-only, and Human-controlled.
- Required output: the patch, artifact, findings, or structured response.
- Acceptance evidence: tests, commands, diffs, logs, or citations the parent can independently inspect.
- Return and stop conditions: when to report COMPLETE or BLOCKED.
If a load-bearing field is missing and cannot be resolved without broadening scope, return BLOCKED instead of guessing.

Surface rules:
- Editable: change only explicitly listed files, directories, systems, or data.
- Locked/read-only: inspect but never modify evaluators, tests, rubrics, policies, or reference surfaces to make the work pass.
- Append-only: append new records without rewriting or deleting prior history.
- Human-controlled: do not merge, deploy, change credentials, alter production state, or perform destructive actions; prepare evidence or a proposal only.
- Treat any unclassified surface as out of scope. Keep unrelated content untouched.

Context discipline:
- Use the compact contract and exact file references as the working context. Do not reconstruct or request the entire noisy parent conversation unless indispensable.
- Prefer targeted reads and file-backed artifacts over copying large logs or tool output into messages.
- Preserve exact load-bearing names, versions, paths, commands, expected values, and user constraints.
- Do not copy secrets into prompts, files, logs, or responses.

Execution and evidence:
- Prefer the smallest complete change or narrowest evidence-gathering path that satisfies the objective.
- Do not redefine the goal, broaden scope, start adjacent work, or make undelegated product/security/architecture decisions.
- Stop before an overlapping write, unsafe action, invalid source, or required scope expansion.
- Run relevant non-destructive checks. Record exact commands and outcomes. Do not claim validation that you did not run.
- Return concise evidence and artifact paths rather than raw intermediate chatter.

Completion policy:
- Return COMPLETE only when the success predicate is satisfied and acceptance evidence is attached.
- Return BLOCKED when required input is missing, the contract is contradictory, or completion would require leaving scope.
- Do not report a partial, narrowed, or answer-shaped result as complete unless the contract explicitly defines it as success.

Special self-check:
- When the delegated objective is exactly SELF_CHECK, do not access or modify project files. Return exactly: LUNA_SUBAGENT_READY:{agent_name}

Return format:
1. Status: COMPLETE or BLOCKED
2. Result
3. Files changed or evidence inspected
4. Acceptance evidence and validation performed
5. Remaining assumptions or risks
"""

    lines = [
        MANAGED_HEADER,
        "# This dedicated file may be replaced by the managing skill after a timestamped backup.",
        f"# Profile: {profile.key} - {profile.purpose}",
        f"name = {toml_basic_string(agent_name)}",
        f"description = {toml_basic_string(description)}",
        f"model = {toml_basic_string(profile.model)}",
        f"model_reasoning_effort = {toml_basic_string(profile.reasoning_effort)}",
    ]
    if profile.service_tier:
        lines.append(f"service_tier = {toml_basic_string(profile.service_tier)}")
    lines.extend(['developer_instructions = """', instructions.rstrip("\n"), '"""'])
    if profile.fast_mode:
        lines.extend(["", "[features]", "fast_mode = true"])
    return "\n".join(lines).rstrip() + "\n"


def build_routing_block(agent_name: str) -> str:
    return f"""{ROUTING_START}
## Sol coordinator and Luna bounded executor

- Keep the primary agent responsible for understanding the request, preserving the overall goal, architecture and scope, choosing approaches, integration, permissions, and final validation.
- Treat subagents primarily as context-isolation and bounded-execution tools. Do not spawn one merely because it is available.
- Prefer `{agent_name}` only when a separate context, parallelism, or specialization materially improves a narrow independent unit enough to justify extra model and tool work.
- Before spawning, define: one objective, source-of-truth inputs, a success predicate, non-counting outcomes, classified surfaces, required output, acceptance evidence, return condition, and stop conditions.
- Classify surfaces as Editable, Locked/read-only, Append-only, or Human-controlled. Treat unclassified surfaces as out of scope.
- Never let a worker modify the evaluator, rubric, policy, or locked tests used to approve its own work.
- Transfer the smallest high-signal context. Prefer exact file references and durable artifacts over copying the parent conversation, large logs, or duplicate tool output.
- Good candidates include targeted file edits, focused tests, read-heavy exploration, extraction, log analysis, independent review, and bounded investigation.
- Keep ambiguous planning, architecture, scope changes, security and permission decisions, merge/deploy approval, destructive actions, and final acceptance in the primary thread.
- Prevent parallel write overlap. Serialize conflicting work or split ownership by non-overlapping files and interfaces.
- For long or parallel runs, keep the root success predicate, approach registry, progress ledger, integration, and adversarial audit with the primary agent.
- Wait for required results, inspect actual artifacts, and independently re-check acceptance evidence. Never accept a subagent completion claim on trust alone.
- Consider total coordinator + worker + verification usage. Multi-agent work can cost more than a direct single-agent run.
{ROUTING_END}
"""


def build_delegation_contract(agent_name: str) -> str:
    return f"""Use the custom agent `{agent_name}`.

Objective:
<one bounded objective>

Why delegation is justified:
<state the context-isolation, parallelism, or specialization benefit; otherwise do not delegate>

Source-of-truth inputs:
- <exact files, refs, commands, data, versions, and freshness>

Success predicate:
- <condition that must be true>
- <condition that must be true>

Does not count:
- <partial artifact, narrowed scope, unsupported claim, or other near miss>

Surfaces:
- Editable: <explicit paths, systems, or data>
- Locked/read-only: <evaluators, tests, policies, and references>
- Append-only: <logs or ledgers; use none when not applicable>
- Human-controlled: <merge, deploy, credentials, production, destructive actions>

Allowed tools and context:
- <tools and network policy>
- <exact context/file references; do not paste unrelated parent history>

Required output:
<patch, artifact, findings, or structured response>

Acceptance evidence:
- <exact tests, commands, diffs, logs, or citations>

Return condition:
- Return COMPLETE only when every success-predicate item is satisfied and evidence is attached.
- Return BLOCKED when a required input is missing or completion would require leaving scope.

Stop conditions:
- Stop before a contradiction, unsafe or human-controlled action, invalid source, scope expansion, or overlapping write.

Return only the status, completed result, artifact paths, acceptance evidence, and remaining risks.
"""
