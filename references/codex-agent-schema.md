# Codex custom-agent compatibility reference

Last reviewed: 2026-08-04

Use current official OpenAI documentation as the source of truth when it differs from this snapshot.

## Mechanism map

| Mechanism | User scope | Project scope | Purpose |
|---|---|---|---|
| Skill | `$HOME/.agents/skills/<skill>/SKILL.md` | `<repo>/.agents/skills/<skill>/SKILL.md` | Reusable workflow instructions and scripts |
| Custom agent | `~/.codex/agents/<name>.toml` | `<repo>/.codex/agents/<name>.toml` | Model and behavior for a spawned subagent |
| Persistent instructions | `~/.codex/AGENTS.md` | `<repo>/AGENTS.md` | Rules loaded into the primary Codex session |

`CODEX_HOME` can replace the default `~/.codex` location.

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

The `name` field, not the filename, is the source of truth. Matching the filename to the name remains the clearest convention.

## Model and effort guidance

- Use `gpt-5.6`/Sol for ambiguous, multi-step coordination and difficult integration.
- Use `gpt-5.6-terra` for efficient read-heavy or supporting work.
- Use `gpt-5.6-luna` for fast, narrow, repeatable, high-volume work.
- Use `medium` as a balanced starting point.
- Use `low` for straightforward latency-sensitive units.
- Reserve `max` for difficult quality-first work that demonstrates a measured benefit.

## Fast-mode caution

Fast mode increases model speed and also increases usage cost. For ChatGPT-authenticated Codex, current documentation says GPT-5.6 Fast mode consumes credits at 2.5 times the Standard rate. For API-key usage, Priority processing has separate pricing; current GPT-5.6 Priority pricing is higher than Standard.

Therefore:

- `gpt-5.6-luna` can lower model cost relative to Sol.
- `model_reasoning_effort = "max"` can increase reasoning use.
- `service_tier = "fast"` increases speed at higher usage cost.
- “Luna Max Fast” is a speed/quality-oriented combination, not the strict minimum-credit combination.

For usage-first bounded work, start with Luna + `medium` + Standard service and measure quality before raising effort or enabling Fast mode.

## Runtime validation

Static validation:

1. Parse TOML.
2. Confirm required fields.
3. Confirm model and effort values.
4. Confirm `service_tier = "fast"` is paired with `[features].fast_mode = true`.
5. Run `codex --version`.

Runtime validation:

1. Start a new Codex session after changing custom-agent files.
2. Use `/agent` to inspect available agent threads and custom-agent discovery.
3. Ask the primary agent to delegate a harmless `SELF_CHECK` objective to the named custom agent.
4. Treat failure to discover the agent as a product/version/surface compatibility issue, not proof that TOML syntax is invalid.

Subagent behavior can vary by Codex surface. Current official documentation describes custom-agent support for local Codex clients. When a surface exposes only generic subagents, named custom agents may not be selectable even though the TOML is valid.

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

## Official documentation locations

- Subagents and custom agents: `https://learn.chatgpt.com/docs/agent-configuration/subagents`
- Skills: `https://learn.chatgpt.com/docs/build-skills`
- AGENTS.md: `https://learn.chatgpt.com/docs/agent-configuration/agents-md`
- Configuration reference: `https://learn.chatgpt.com/docs/config-file/config-reference`
- Fast mode: `https://learn.chatgpt.com/docs/agent-configuration/speed`
