# Codex custom-agent compatibility reference

Last reviewed: 2026-08-04

Use current official OpenAI documentation as the source of truth when it differs from this snapshot. OpenAI notes that custom-agent authoring may evolve.

## Mechanism map

| Mechanism | User scope | Project scope | Purpose |
|---|---|---|---|
| Skill | `$HOME/.agents/skills/<skill>/SKILL.md` | `<repo>/.agents/skills/<skill>/SKILL.md` | Reusable workflow instructions and scripts |
| Custom agent | `~/.codex/agents/<name>.toml` | `<repo>/.codex/agents/<name>.toml` | Model and behavior for a spawned subagent |
| Persistent instructions | `~/.codex/AGENTS.md` | `<repo>/AGENTS.md` | Rules loaded into the primary Codex session |

`CODEX_HOME` can replace the default `~/.codex` location.

Codex reads `AGENTS.override.md` before `AGENTS.md` at a scope and uses the first non-empty file there. Project instructions are layered from the project root toward the working directory.

## Current custom-agent schema

A standalone custom-agent TOML file requires:

```toml
name = "agent-name"
description = "When the coordinator should use this agent."
developer_instructions = """
The agent's behavioral boundaries and return contract.
"""
```

Supported session-level overrides can include:

```toml
model = "gpt-5.6-luna"
model_reasoning_effort = "medium"
service_tier = "fast"

[features]
fast_mode = true
```

Other supported `config.toml` settings, including `sandbox_mode`, MCP servers, and skill configuration, may also appear in a custom-agent file. Omitted session settings inherit according to Codex's current parent/default resolution rules.

The `name` field, not the filename, is the source of truth. Matching the filename to the name remains the clearest convention.

## Model and effort guidance

Current official guidance:

- Use `gpt-5.6`/Sol for ambiguous, multi-step planning, validation, and demanding integration.
- Use `gpt-5.6-terra` for efficient read-heavy supporting work.
- Use `gpt-5.6-luna` for fast, narrowly scoped, clear, repeatable, or high-volume work.
- Use `medium` as a balanced default.
- Use `low` for straightforward latency-sensitive units.
- Reserve `max` or `xhigh` for tasks that demonstrate a quality benefit.

Higher reasoning effort increases latency and token usage.

## Fast-mode caution

For ChatGPT-authenticated Codex:

- GPT-5.6 Fast mode increases supported model speed and consumes credits at 2.5 times the Standard rate.
- Persist Fast mode with `service_tier = "fast"` plus `[features].fast_mode = true`.
- Fast mode is distinct from selecting a separate fast model.

For API-key usage:

- ChatGPT credit multipliers do not apply.
- GPT-5.6 API Priority processing currently costs 2 times the Standard API token rate.

Therefore:

- `gpt-5.6-luna` can lower model cost relative to Sol.
- `model_reasoning_effort = "max"` can increase reasoning use.
- `service_tier = "fast"` increases speed at higher usage cost.
- “Luna Max Fast” is a speed/quality combination, not the strict minimum-credit combination.

For usage-first bounded work, start with Luna + `medium` + Standard service and measure quality before raising effort or enabling Fast mode.

## Delegation economics and context

Official Codex guidance states that each subagent performs separate model and tool work, so subagent workflows consume more tokens than comparable single-agent runs. Use subagents when independent work, context isolation, or parallel execution materially improves speed or quality.

Start with read-heavy or isolated work. Be more cautious with parallel write-heavy workflows because edit conflicts and coordination overhead can erase the benefit.

## Generated contract and guardrails

This Skill's managed agent requires:

- Objective and source-of-truth inputs.
- Success predicate and non-counting outcomes.
- Editable, locked/read-only, append-only, and human-controlled surfaces.
- Required output and acceptance evidence.
- Explicit COMPLETE, BLOCKED, and stop conditions.

Print a copyable contract without changing configuration:

```bash
python <skill-dir>/scripts/configure_luna_agent.py contract --profile economy
```

## Runtime validation

Static validation:

1. Parse TOML.
2. Confirm required fields.
3. Confirm model and effort values.
4. Confirm `service_tier = "fast"` is paired with `[features].fast_mode = true`.
5. Confirm managed delegation guardrails.
6. Run `codex --version`.

Runtime validation:

1. Start a new Codex session after changing custom-agent files.
2. Use `/agent` to inspect available agent threads and custom-agent discovery.
3. Ask the primary agent to delegate a harmless `SELF_CHECK` objective to the named custom agent.
4. Treat failure to discover the agent as a product/version/surface compatibility issue, not proof that TOML syntax is invalid.

Custom-agent support is documented for local Codex clients. A surface may expose generic subagents without allowing selection of a named custom agent.

## Windows notes

`~/.codex/agents/luna-max-fast.toml` normally resolves to:

```text
C:\Users\<username>\.codex\agents\luna-max-fast.toml
```

A user-installed Skill normally resolves to:

```text
C:\Users\<username>\.agents\skills\codex-luna-delegation\SKILL.md
```

PowerShell does not use Bash `\` line continuation. Put the command on one line or use PowerShell backticks.

When Codex runs inside WSL, `~` refers to the Linux home directory, not the Windows profile directory. Install the custom agent in the environment where the active Codex process reads its configuration.

## Official documentation

- Subagents and custom agents: `https://developers.openai.com/codex/agent-configuration/subagents`
- Skills: `https://developers.openai.com/codex/build-skills`
- AGENTS.md: `https://developers.openai.com/codex/agent-configuration/agents-md`
- Configuration reference: `https://developers.openai.com/codex/config-reference`
- Fast mode: `https://developers.openai.com/codex/agent-configuration/speed`
- GPT-5.6 model guidance: `https://developers.openai.com/api/docs/guides/latest-model`
- Codex rate card: `https://help.openai.com/en/articles/20001106-codex-rate-card-2`
