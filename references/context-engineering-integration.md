# Context-engineering integration boundary

Last reviewed: 2026-08-04

## Purpose

This repository intentionally uses a thin integration model. `codex-luna-delegation` remains a focused Codex implementation Skill instead of absorbing an entire context-engineering curriculum.

The design was informed by:

- `muratcankoylan/Agent-Skills-for-Context-Engineering`
- Reviewed commit: `a1841d1ea3dadc70098d94b60fa7a4ab8875dc50`
- Upstream license: MIT
- Copyright: 2025 Context Engineering Agent Skills Contributors

Upstream repository:
`https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering`

No upstream Skill is copied wholesale. The rules below are a Codex-specific, independently worded adaptation of a small subset of compatible principles.

## Concepts adapted

1. **Context isolation is the primary reason to use a subagent.**
   Delegation should move noisy exploration, logs, tests, or a bounded implementation slice away from the coordinator context.

2. **Multi-agent overhead must be justified.**
   A worker adds its own model context, tools, handoff, and verification work. Small tasks should remain in the primary thread.

3. **Instruction passing is the default.**
   Pass a compact contract rather than the entire parent conversation. Use exact file references and durable artifacts for large shared state.

4. **A delegated unit needs a checkable completion contract.**
   Define the success predicate, non-counting outcomes, required artifact, evidence, and return condition before execution.

5. **Surfaces require explicit governance.**
   Separate editable, locked/read-only, append-only, and human-controlled surfaces. A worker must not weaken the evaluator used to approve its own output.

6. **The coordinator owns integration and final acceptance.**
   Worker output is evidence, not authority. The primary thread re-checks critical claims and resolves conflicts.

## Deliberately excluded

This Skill does not own or reproduce:

- General supervisor, swarm, or hierarchical topology selection.
- System-wide context compression, observation masking, KV-cache, or retrieval-budget design.
- Full long-horizon autonomous prompt design.
- General memory systems, BDI architecture, tool-design theory, or evaluation frameworks.
- Framework-specific LangGraph, AutoGen, or CrewAI implementation guidance.
- Unverified numerical token multipliers or universal worker-count thresholds.

Use separate Skills for those topics. Keeping ownership separate preserves progressive disclosure and reduces accidental trigger overlap.

## Ownership map

| Concern | Owning Skill or layer |
|---|---|
| Whether a multi-agent topology is justified | `multi-agent-patterns` |
| System-wide context and token optimization | `context-optimization` |
| Root brief for long autonomous work | `long-horizon-prompting` |
| Locked surfaces, ledgers, rollback, approval governance | `harness-engineering` |
| Codex Luna TOML, profiles, routing, contract, validation | `codex-luna-delegation` |

## Implementation in this repository

- `SKILL.md` contains the delegation decision gate, context-transfer policy, surface model, and orchestration workflow.
- `scripts/configure_luna_agent.py` emits those rules into the managed Luna TOML and `AGENTS.md` routing block.
- The script's `contract` command prints a reusable bounded delegation brief.
- `tests/test_configure_luna_agent.py` verifies profile generation, guardrails, routing preservation, and contract structure.
