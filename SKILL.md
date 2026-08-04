---
name: codex-luna-delegation
description: "Configure, validate, or operate a Codex Sol-coordinator/Luna-subagent workflow. Use for gpt-5.6-luna custom-agent TOML, bounded delegation contracts, context-isolated worker tasks, AGENTS.md routing, profile and credit tradeoffs, dry-run diffs, runtime discovery, or troubleshooting luna-max-fast/luna-economy. Do not use for generic multi-agent architecture, broad context-engineering theory, or unrelated coding tasks."
---

# Codex Luna Delegation

Use a strong primary agent as coordinator and a narrow GPT-5.6 Luna custom agent as executor. Treat subagents primarily as **context-isolation and bounded-execution tools**, not as role-play or an automatic speedup. Keep the overall goal, architecture, planning, integration, permissions, and final acceptance in the primary thread.

## Scope and related skills

This Skill owns the Codex-specific implementation layer:

- Create and maintain a Luna custom-agent TOML file.
- Install a persistent Sol/Luna routing block without damaging unrelated configuration.
- Select `exact`, `economy`, or `fast-balanced` profiles.
- Decide whether a concrete unit is safe and worthwhile to delegate.
- Produce a complete delegation contract.
- Validate static configuration and optional runtime discovery.

Keep broader concerns separate:

- Use `multi-agent-patterns` to choose supervisor, swarm, or hierarchical topology.
- Use `context-optimization` for system-wide masking, compaction, caching, and token-budget policy.
- Use `long-horizon-prompting` for the root brief of an autonomous, open-ended run.
- Use `harness-engineering` for locked evaluators, durable ledgers, rollback, and approval governance.

When those skills are installed, use them for upstream design and this Skill for the Codex/Luna execution layer. Do not copy their full content into this Skill. See [references/context-engineering-integration.md](references/context-engineering-integration.md).

## Distinguish the three mechanisms

Do not confuse these files:

- **Skill:** this folder and its `SKILL.md`; defines the reusable workflow.
- **Custom agent:** `~/.codex/agents/<name>.toml` or `.codex/agents/<name>.toml`; defines the spawned Luna session.
- **Persistent routing policy:** `~/.codex/AGENTS.md` or project `AGENTS.md`; tells future primary sessions when and how to delegate.

A Skill does not become the custom agent. Use this Skill to create and maintain the separate TOML definition and, when requested, the routing policy.

## Select the operating mode

1. **Setup or maintenance**
   - Create, update, inspect, validate, or troubleshoot the custom agent.
   - Follow the setup workflow.

2. **Active Sol/Luna task**
   - Keep planning and integration in the primary thread.
   - Pass the delegation decision gate.
   - Give Luna a complete bounded contract.
   - Inspect the returned artifact and evidence before accepting it.

3. **Contract generation**
   - Produce a copyable delegation brief without changing configuration.
   - Use the script's `contract` command or the template in this Skill.

4. **Usage or credit optimization**
   - Explain the profile tradeoff before choosing silently.
   - Use `economy` when lower usage is the actual priority.
   - Use `exact` only when the user explicitly wants Luna + Max + Fast.
   - Evaluate total coordinator + worker + verification usage, not Luna's model rate alone.

## Profile choices

| Profile | Model | Reasoning | Service tier | Purpose |
|---|---|---|---|---|
| `exact` | `gpt-5.6-luna` | `max` | `fast` | Match “Luna Max Fast” exactly. Quality/speed first. |
| `economy` | `gpt-5.6-luna` | `medium` | standard/default | Prefer for usage-conscious bounded work. |
| `fast-balanced` | `gpt-5.6-luna` | `medium` | `fast` | Prefer when speed matters but routine work does not need maximum reasoning. |

Do not describe `exact` as the cheapest setup. Higher reasoning effort increases token use, and GPT-5.6 Fast mode consumes ChatGPT credits at 2.5 times the Standard rate. Luna is cost-oriented, but `max` and `fast` offset part of that advantage. API-key sessions use API pricing rather than ChatGPT credit multipliers.

## Delegation decision gate

Delegate only when a separate worker context creates a material benefit that exceeds coordination overhead. A unit must satisfy **all** of these conditions:

1. It has one clear objective.
2. The source-of-truth inputs are explicit and current.
3. A success predicate defines what must be true at completion.
4. Non-counting outcomes identify plausible near misses that must not be reported as complete.
5. Editable, locked, append-only, and human-controlled surfaces are explicit.
6. Required output and acceptance evidence are defined.
7. The unit can finish without changing the overall goal or architecture.
8. It does not require product, security, permission, deployment, merge, or destructive-action decisions.
9. Its writes do not overlap with another active agent.
10. The primary thread can independently inspect or validate the result.
11. Context isolation, parallelism, or specialization is worth the extra model/tool work.

Do not delegate when:

- The primary agent can complete the task directly with less overhead.
- The request is ambiguous or still needs scope discovery.
- The work is highly coupled across many files or systems.
- The worker would need to change the evaluator, rubric, or acceptance bar to pass.
- No independent evidence can establish completion.
- The only benefit is “an agent is available.”

Good candidates include targeted file edits, focused tests, read-heavy exploration, extraction, log analysis, isolated reviews, or a well-defined implementation slice. Keep architecture, cross-cutting integration, security decisions, deploy/merge approval, and final acceptance in the primary thread.

## Context transfer policy

Use the smallest high-signal context that preserves correctness:

1. **Instruction passing is the default.** Send a compact contract containing only the objective, source-of-truth inputs, constraints, surfaces, output, and checks.
2. **Use files for bulky or durable state.** Point Luna to exact paths for specifications, logs, test output, or intermediate artifacts instead of pasting them into the delegation message.
3. **Use full-context delegation only as an exception.** State why the unit cannot be completed safely from a compact contract, and still exclude unrelated history.
4. **Do not dump the parent conversation.** Remove brainstorming, superseded decisions, duplicate tool output, and unrelated stack traces.
5. **Preserve exact facts.** Keep filenames, symbols, versions, commands, expected values, and user constraints verbatim when they are load-bearing.
6. **Mark source and freshness.** Identify which file, branch, issue, or command output is authoritative and whether it may be stale.
7. **Do not duplicate secrets.** Reference approved credential mechanisms; never copy credentials into a worker prompt or artifact.

## Surface classification

Every write-capable delegation must classify its surfaces:

| Surface | Meaning | Luna rule |
|---|---|---|
| **Editable** | Files or data explicitly in scope | May change only these surfaces. |
| **Locked/read-only** | Tests, evaluators, rubrics, policies, or reference files used to judge the work | May inspect but must not change them to make the task pass. |
| **Append-only** | Logs, result ledgers, research notes | May append; must not rewrite or erase prior history. |
| **Human-controlled** | Merge, deploy, credentials, production state, destructive actions | May prepare evidence or a proposal; must not execute the action. |

If a surface is not classified, treat it as out of scope.

## Delegation contract

Generate a complete template with:

```bash
python <skill-dir>/scripts/configure_luna_agent.py contract \
  --profile economy
```

Use the resulting structure:

```text
Use the custom agent <agent-name>.

Objective:
<one bounded objective>

Why delegation is justified:
<context isolation, parallelism, or specialization benefit>

Source-of-truth inputs:
<exact files, refs, commands, data, versions, and freshness>

Success predicate:
<conditions that must all be true>

Does not count:
<near misses, partial artifacts, narrowed scope, or unsupported claims>

Surfaces:
- Editable: <explicit paths/systems>
- Locked/read-only: <evaluators, tests, policies, references>
- Append-only: <logs or ledgers>
- Human-controlled: <merge, deploy, credentials, destructive actions>

Allowed tools and context:
<tools, network policy, and exact context references>

Required output:
<patch, artifact, findings, or structured response>

Acceptance evidence:
<tests, commands, diffs, logs, or citations>

Return condition:
Return COMPLETE only when the success predicate is satisfied and evidence is attached.
Return BLOCKED when a required input is missing or the task cannot be completed inside scope.

Stop conditions:
<contradiction, scope expansion, unsafe action, overlapping write, or invalid source>
```

Do not weaken the contract merely to avoid a `BLOCKED` result. A truthful blocker is better than an answer-shaped near miss.

## Long-horizon and parallel work

For an open-ended or multi-worker run:

- Keep the root success predicate, approach selection, progress ledger, integration, and final audit with Sol.
- Delegate bounded slices, not the entire ambiguous problem, unless a separate long-horizon Skill and harness define the root run.
- Store shared state in durable files when multiple workers need exact access; avoid repeated paraphrasing through the coordinator.
- Preserve early independence between exploratory workers and prevent duplicate approaches.
- Mark blocked routes and verified findings explicitly so later workers do not rediscover the same dead end.
- Use fresh-context verification for critical results when practical; do not let the author silently approve its own evaluator changes.
- Serialize overlapping writes or split ownership by non-overlapping files and interfaces.
- Wait for all required workers before synthesis, but do not wait for optional work that no longer affects the predicate.

## Orchestration workflow

For an active task:

1. Understand the whole request in the primary thread.
2. Define the overall goal, architecture boundaries, and human-controlled actions.
3. Identify zero or more independent units.
4. Apply the delegation decision gate; keep small or coupled work in the primary thread.
5. Build a complete contract for each accepted unit.
6. Transfer only high-signal context and exact file references.
7. Spawn `luna-max-fast`, `luna-economy`, `luna-fast`, or the explicitly configured agent.
8. Prevent overlapping writes and track active ownership.
9. Wait for required results and inspect the actual artifacts, not only summaries.
10. Re-run or independently check the stated acceptance evidence.
11. Resolve conflicts and perform integration tests in the primary thread.
12. Deliver one integrated result; do not forward raw subagent chatter or unverified completion claims.

## Setup workflow

### 1. Inspect before writing

- Run `codex --version` when available.
- Resolve `CODEX_HOME`; default to `~/.codex` when unset.
- Inspect the target custom-agent file.
- Inspect the active global or project instruction file. A non-empty `AGENTS.override.md` takes precedence over `AGENTS.md`.
- Never overwrite `~/.codex/config.toml`, other custom agents, or unrelated instruction content.

### 2. Preview the exact diff

Resolve this Skill's directory from the loaded `SKILL.md` path. Run its script with an absolute path.

Quoted Luna Max Fast setup:

```bash
python <skill-dir>/scripts/configure_luna_agent.py install \
  --profile exact \
  --scope user \
  --routing global \
  --dry-run
```

Usage-first setup:

```bash
python <skill-dir>/scripts/configure_luna_agent.py install \
  --profile economy \
  --scope user \
  --routing global \
  --dry-run
```

On Windows PowerShell, use one line or PowerShell backticks rather than Bash backslashes. Review the unified diff and confirm that only the dedicated agent file and marked routing block change.

### 3. Apply the configuration

Run the same command without `--dry-run`.

The script must:

- Create a timestamped backup before changing an existing file.
- Refuse to replace an unmanaged target agent file unless `--force` is explicitly used after inspection.
- Update only the block between `codex-luna-delegation` markers in `AGENTS.md`.
- Leave all other configuration and instructions unchanged.

Project-scoped example:

```bash
python <skill-dir>/scripts/configure_luna_agent.py install \
  --profile exact \
  --scope project \
  --routing project \
  --project-root <repo-root>
```

### 4. Validate statically

```bash
python <skill-dir>/scripts/configure_luna_agent.py validate \
  --profile exact \
  --scope user
```

Require all of the following:

- TOML parses successfully when a TOML parser is available.
- `name`, `description`, and `developer_instructions` are present and non-empty.
- Model, reasoning effort, service tier, and Fast-mode pairing match the selected profile.
- Managed files contain the delegation contract and surface guardrails.
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

State before running it that this starts a real Codex turn and may consume ChatGPT credits or API tokens. Treat the smoke test as discovery evidence, not proof of exact billing or internal routing.

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
- Delegation guardrails: PASS/FAIL
- Runtime discovery: PASS / NOT RUN / FAIL

Important tradeoff
- <usage-first or speed/quality-first; include Fast-mode multiplier when relevant>

Next use
- <one concrete contract or invocation example>
```

Include the generated diff when changes were applied or requested.

## Compatibility and troubleshooting

Read [references/codex-agent-schema.md](references/codex-agent-schema.md) when:

- The installed Codex version rejects the TOML.
- The agent does not appear under `/agent`.
- Fast mode is unavailable.
- The user is on Windows or WSL and the resolved home path is unclear.
- Current official documentation may have changed.

Use current official OpenAI documentation as the source of truth. Report a docs/runtime mismatch instead of inventing a compatible format.
