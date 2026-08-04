---
name: codex-luna-delegation
description: "Configure, update, validate, or troubleshoot a Codex Sol-coordinator/Luna-subagent workflow. Use when the user asks to create or repair ~/.codex/agents/luna-max-fast.toml, use gpt-5.6-luna for bounded delegated work, preserve existing Codex configuration, add a persistent AGENTS.md routing policy, show a diff, verify the installed Codex version, or mentions Sol 統籌, Luna 子代理, luna-max-fast, Codex 省額度, Max, or Fast mode. Also use to orchestrate a task with Sol planning and Luna executing narrow independent units. Do not use for generic model selection or unrelated coding tasks."
---

# Codex Luna Delegation

Use a strong primary agent as coordinator and a narrow GPT-5.6 Luna custom agent as executor. Keep the overall goal, decomposition, integration, and final validation in the primary thread. Move only clear, independent work into the subagent.

## Distinguish the three mechanisms

Do not confuse these files:

- **Skill:** this folder and its `SKILL.md`; installs or applies the workflow.
- **Custom agent:** `~/.codex/agents/<name>.toml` or `.codex/agents/<name>.toml`; defines the spawned subagent.
- **Persistent routing policy:** `~/.codex/AGENTS.md` or a project `AGENTS.md`; tells future primary sessions when to delegate.

A Skill does not become the custom agent. Use this Skill to create and maintain the separate TOML agent definition and, when requested, the routing policy.

## Select the operating mode

1. **Setup or maintenance request**
   - Create, update, inspect, validate, or troubleshoot the custom agent.
   - Follow the setup workflow below.

2. **Active Sol/Luna task request**
   - Keep planning and integration in the primary thread.
   - Verify the custom agent exists before delegation.
   - Delegate only units that satisfy every boundary rule below.
   - Wait for results, inspect them, and perform final validation in the primary thread.

3. **Usage or credit optimization request**
   - Explain the profile tradeoff before choosing silently.
   - Use `economy` when lower usage is the actual priority.
   - Use `exact` only when the user explicitly wants Luna + Max + Fast.

## Profile choices

Use one of these profiles:

| Profile | Model | Reasoning | Service tier | Purpose |
|---|---|---|---|---|
| `exact` | `gpt-5.6-luna` | `max` | `fast` | Match the quoted “Luna Max Fast” setup exactly. Quality/speed first. |
| `economy` | `gpt-5.6-luna` | `medium` | standard/default | Prefer for genuinely usage-conscious bounded work. |
| `fast-balanced` | `gpt-5.6-luna` | `medium` | `fast` | Prefer when speed matters but routine work does not need maximum reasoning. |

Do not describe `exact` as the cheapest setup. Maximum reasoning can use more reasoning tokens, and Fast mode consumes more credits or higher-priority API pricing. Luna itself is cost-oriented, but `max` and `fast` partially offset that benefit.

## Setup workflow

### 1. Inspect before writing

- Run `codex --version` when available.
- Resolve `CODEX_HOME`; default to `~/.codex` when it is unset.
- Inspect the target custom-agent file.
- Inspect the active global or project instruction file. An existing non-empty `AGENTS.override.md` takes precedence over `AGENTS.md`.
- Never overwrite `~/.codex/config.toml`, other custom agents, or unrelated instruction content.

### 2. Preview the exact diff

Resolve this Skill's directory from the loaded `SKILL.md` path. Run its script with an absolute path.

For the quoted setup at user scope with persistent global routing:

```bash
python <skill-dir>/scripts/configure_luna_agent.py install \
  --profile exact \
  --scope user \
  --routing global \
  --dry-run
```

For actual usage-first routing:

```bash
python <skill-dir>/scripts/configure_luna_agent.py install \
  --profile economy \
  --scope user \
  --routing global \
  --dry-run
```

On Windows PowerShell, use one line or PowerShell backticks rather than Bash backslashes.

Review the unified diff. Confirm that only the dedicated agent file and the marked routing block will change.

### 3. Apply the configuration

Run the same command without `--dry-run`.

The script must:

- Create a timestamped backup before changing an existing file.
- Refuse to replace an unmanaged target agent file unless `--force` is explicitly used after inspection.
- Update only the block between `codex-luna-delegation` markers in `AGENTS.md`.
- Leave all other configuration and instructions unchanged.

Use project scope when the workflow should apply only to one repository:

```bash
python <skill-dir>/scripts/configure_luna_agent.py install \
  --profile exact \
  --scope project \
  --routing project \
  --project-root <repo-root>
```

### 4. Validate statically

Run:

```bash
python <skill-dir>/scripts/configure_luna_agent.py validate \
  --profile exact \
  --scope user
```

Require all of the following:

- TOML parses successfully when a TOML parser is available.
- `name`, `description`, and `developer_instructions` are present and non-empty.
- The selected model, reasoning effort, and Fast-mode pairing match the requested profile.
- `codex --version` succeeds when Codex is installed on `PATH`.

Do not claim runtime compatibility merely because TOML parsing passed.

### 5. Validate runtime discovery

Prefer a new Codex session, then use `/agent` to confirm that the named custom agent appears.

Only when the user explicitly requests a real smoke test, run:

```bash
python <skill-dir>/scripts/configure_luna_agent.py validate \
  --profile exact \
  --scope user \
  --smoke-test
```

State before running it that this starts a real Codex turn and may consume ChatGPT credits or API tokens. Treat the smoke test as evidence of discovery, not proof of exact billing or internal model routing.

### 6. Report the result

Use this structure:

```text
Configuration result
- Codex version: <detected version or unavailable>
- Agent file: <path>
- Routing policy: <path or not installed>
- Profile: <profile and settings>
- Backups: <paths or none>

Validation
- TOML/schema: PASS/FAIL
- Required agent fields: PASS/FAIL
- Runtime discovery: PASS / NOT RUN / FAIL

Important tradeoff
- <state whether the selected profile is usage-first or speed/quality-first>

Next use
- <one concrete invocation example>
```

Include the generated diff when the user asks for it or when changes were applied.

## Delegation boundary rules

Delegate to the Luna custom agent only when **all** of these are true:

1. The unit has one clear objective.
2. Inputs and required outputs are explicit.
3. Allowed files, systems, or data are bounded.
4. Acceptance checks are defined.
5. The unit can complete without changing the overall goal.
6. The unit does not require architecture, product, security, permission, or destructive-action decisions.
7. Its writes do not overlap with another active agent.
8. The primary thread can independently inspect or validate the result.

Good candidates:

- Modify one named function or a small listed set of files.
- Add focused unit tests for a defined behavior.
- Run a bounded test suite and summarize failures.
- Extract defined fields from a known set of files.
- Investigate one error path and return evidence.
- Review one isolated module against explicit criteria.

Keep in the primary thread:

- Understanding an ambiguous request.
- Choosing architecture or changing scope.
- Coordinating changes across many coupled modules.
- Deciding security, access, deployment, or destructive actions.
- Integrating conflicting findings.
- Performing final acceptance and communicating the result.

## Delegation prompt template

Give the subagent a complete, bounded contract:

```text
Use the custom agent <agent-name>.

Objective:
<one objective>

Allowed scope:
<files, directories, systems, or data it may touch>

Do not:
<explicit exclusions>

Required output:
<artifact, patch, findings, or structured response>

Acceptance checks:
<tests or evidence required>

Return only the completed result, validation performed, and remaining risks.
```

Do not send the entire noisy parent conversation when a compact task contract is sufficient. Preserve only the context required to complete the unit.

## Orchestration workflow

For an active task:

1. Analyze the whole request in the primary thread.
2. Define the overall plan and non-negotiable constraints.
3. Identify zero or more independent bounded units.
4. Avoid delegation when the task is already small; a subagent adds separate model and tool work.
5. Spawn `luna-max-fast`, `luna-economy`, or the explicitly configured agent for each suitable unit.
6. Avoid parallel writes to the same files.
7. Wait for all required results.
8. Inspect diffs, evidence, and validation claims.
9. Resolve conflicts and perform final tests in the primary thread.
10. Deliver one integrated result; do not forward raw subagent chatter.

## Compatibility and troubleshooting

Read [references/codex-agent-schema.md](references/codex-agent-schema.md) when:

- The installed Codex version rejects the TOML.
- The agent does not appear under `/agent`.
- Fast mode is unavailable.
- The user is on Windows or WSL and the resolved home path is unclear.
- Current official documentation may have changed.

Use current official OpenAI documentation as the source of truth when network access is available. Report any docs/runtime mismatch instead of inventing a compatible format.
