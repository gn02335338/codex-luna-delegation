#!/usr/bin/env python3
"""Safely configure and validate a bounded GPT-5.6 Luna Codex subagent.

The script only manages:
  * one dedicated custom-agent TOML file, and
  * one marked routing block inside an active AGENTS.md file (optional).

It never edits ~/.codex/config.toml and never deletes unrelated agents or
instructions. Existing files are backed up before changes are written.
"""

from __future__ import annotations

import argparse
import difflib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

try:  # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - depends on local Python
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:  # pragma: no cover - handled at runtime
        tomllib = None  # type: ignore[assignment]


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
        purpose="Matches the requested Luna Max + Fast combination; quality/speed first, not minimum-credit mode.",
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
        purpose="Faster bounded execution without using maximum reasoning on routine work.",
    ),
}


class ConfigError(RuntimeError):
    """Raised for safe, user-actionable configuration errors."""


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ConfigError(f"Cannot safely edit non-UTF-8 file: {path}") from exc


def ensure_trailing_newline(text: str) -> str:
    return text if not text or text.endswith("\n") else text + "\n"


def backup_file(path: Path) -> Path | None:
    if not path.exists():
        return None
    candidate = path.with_name(f"{path.name}.bak.{utc_stamp()}")
    counter = 1
    while candidate.exists():
        candidate = path.with_name(f"{path.name}.bak.{utc_stamp()}.{counter}")
        counter += 1
    shutil.copy2(path, candidate)
    return candidate


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def unified_diff(path: Path, before: str, after: str) -> str:
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)
    diff = difflib.unified_diff(
        before_lines,
        after_lines,
        fromfile=f"{path} (before)",
        tofile=f"{path} (after)",
    )
    rendered = "".join(diff)
    return rendered if rendered else "(no changes)\n"


def resolve_codex_home() -> Path:
    override = os.environ.get("CODEX_HOME", "").strip()
    return Path(override).expanduser().resolve() if override else (Path.home() / ".codex").resolve()


def detect_project_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        candidate = completed.stdout.strip()
        if candidate:
            return Path(candidate).resolve()
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass
    return Path.cwd().resolve()


def resolve_agent_path(scope: str, agent_name: str, project_root: Path) -> Path:
    if scope == "user":
        return resolve_codex_home() / "agents" / f"{agent_name}.toml"
    return project_root / ".codex" / "agents" / f"{agent_name}.toml"


def first_nonempty_override(base_path: Path) -> Path:
    override = base_path.with_name("AGENTS.override.md")
    if override.exists() and read_text(override).strip():
        return override
    return base_path


def resolve_routing_path(routing: str, project_root: Path) -> Path | None:
    if routing == "none":
        return None
    if routing == "global":
        return first_nonempty_override(resolve_codex_home() / "AGENTS.md")
    return first_nonempty_override(project_root / "AGENTS.md")


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
        "Execution-focused GPT-5.6 Luna subagent for narrow, independent tasks with explicit inputs, "
        "outputs, boundaries, and acceptance checks. Use for bounded implementation, targeted tests, "
        "file-level edits, extraction, or focused investigation. Do not use for planning, architecture, "
        "scope changes, cross-cutting decisions, or ambiguous work."
    )
    instructions = f"""You are {agent_name}, an execution-focused subagent.

Operating boundaries:
- Execute only the delegated objective. Treat the parent agent's goal, scope, inputs, outputs, constraints, allowed files, and acceptance criteria as fixed.
- Do not redefine the overall goal, broaden the task, start adjacent work, or make architecture/product decisions that were not delegated.
- Do not spawn additional agents.
- Do not modify files outside the explicitly delegated scope. Keep unrelated content untouched.
- Prefer the smallest complete change or the narrowest evidence-gathering path that satisfies the objective.
- Run relevant non-destructive checks for the work you performed. Do not claim validation that you did not run.
- If a required input is missing or the task cannot be completed within scope, stop and return: BLOCKED, the missing information, and the safest next action. Do not guess your way into a wider task.

Special self-check:
- When the delegated objective is exactly SELF_CHECK, do not access or modify project files. Return exactly: LUNA_SUBAGENT_READY:{agent_name}

Return format:
1. Result
2. Files changed or evidence inspected
3. Validation performed
4. Remaining assumptions or risks
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
    lines.extend(
        [
            'developer_instructions = """',
            instructions.rstrip("\n"),
            '"""',
        ]
    )
    if profile.fast_mode:
        lines.extend(["", "[features]", "fast_mode = true"])
    return "\n".join(lines).rstrip() + "\n"


def build_routing_block(agent_name: str) -> str:
    return f"""{ROUTING_START}
## Sol coordinator and Luna executor

- Keep the primary agent responsible for understanding the request, preserving the overall goal, planning, decomposition, cross-task decisions, integration, and final validation.
- Prefer the custom `{agent_name}` subagent only for a delegated unit that is narrow, independent, and has explicit inputs, outputs, boundaries, and acceptance checks.
- Good delegation candidates include targeted file edits, bounded implementation, focused investigation, test execution, extraction, and independent review work.
- Do not delegate ambiguous planning, architecture, scope changes, destructive actions, security or permission decisions, or write-heavy tasks that overlap with another agent.
- Give every delegation a single objective, allowed scope/files, required output, constraints, and validation criteria.
- Wait for the result, inspect it, and keep final responsibility in the primary thread. Do not accept a subagent claim without appropriate verification.
- Do not spawn a subagent merely because one is available. Each subagent performs separate model and tool work and can increase total credit/token usage.
{ROUTING_END}
"""


def upsert_marked_block(existing: str, block: str) -> str:
    start = existing.find(ROUTING_START)
    end = existing.find(ROUTING_END)
    if (start == -1) != (end == -1):
        raise ConfigError(
            "Found only one routing marker in AGENTS.md. Repair the marker pair manually before continuing."
        )
    if start != -1 and end != -1:
        if end < start:
            raise ConfigError("Routing markers are out of order in AGENTS.md.")
        end += len(ROUTING_END)
        prefix = existing[:start].rstrip()
        suffix = existing[end:].lstrip("\r\n")
        pieces = [piece for piece in (prefix, block.rstrip(), suffix.rstrip()) if piece]
        return "\n\n".join(pieces).rstrip() + "\n"

    existing_clean = existing.rstrip()
    if existing_clean:
        return existing_clean + "\n\n" + block.rstrip() + "\n"
    return block.rstrip() + "\n"


def parse_toml(content: str) -> Mapping[str, Any] | None:
    if tomllib is None:
        return None
    try:
        parsed = tomllib.loads(content)
    except Exception as exc:  # tomllib/TOMLDecodeError varies by implementation
        raise ConfigError(f"TOML parse failed: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ConfigError("TOML root must be a table/object.")
    return parsed


def validate_agent_content(
    content: str,
    expected_name: str | None = None,
    expected_profile: Profile | None = None,
) -> list[str]:
    messages: list[str] = []
    data = parse_toml(content)
    if data is None:
        required_patterns = {
            "name": r"(?m)^name\s*=\s*\".+\"\s*$",
            "description": r"(?m)^description\s*=\s*\".+\"\s*$",
            "developer_instructions": r"(?m)^developer_instructions\s*=\s*\"\"\"",
        }
        missing = [key for key, pattern in required_patterns.items() if not re.search(pattern, content)]
        if missing:
            raise ConfigError(f"Structural validation failed; missing: {', '.join(missing)}")

        if expected_name:
            name_pattern = rf'(?m)^name\s*=\s*{re.escape(toml_basic_string(expected_name))}\s*$'
            if not re.search(name_pattern, content):
                raise ConfigError(f"Agent name does not match expected value: {expected_name!r}.")

        if expected_profile:
            expected_pairs = {
                "model": expected_profile.model,
                "model_reasoning_effort": expected_profile.reasoning_effort,
            }
            if expected_profile.service_tier:
                expected_pairs["service_tier"] = expected_profile.service_tier
            for key, value in expected_pairs.items():
                pattern = rf'(?m)^{re.escape(key)}\s*=\s*{re.escape(toml_basic_string(value))}\s*$'
                if not re.search(pattern, content):
                    raise ConfigError(
                        f"Profile mismatch: expected `{key} = {toml_basic_string(value)}` for profile "
                        f"{expected_profile.key!r}."
                    )
            has_service_tier = re.search(r"(?m)^service_tier\s*=", content) is not None
            has_fast_mode = re.search(r"(?m)^fast_mode\s*=\s*true\s*$", content) is not None
            if expected_profile.service_tier is None and has_service_tier:
                raise ConfigError(
                    f"Profile mismatch: profile {expected_profile.key!r} expects no explicit `service_tier`."
                )
            if has_fast_mode is not expected_profile.fast_mode:
                raise ConfigError(
                    f"Profile mismatch: profile {expected_profile.key!r} expects "
                    f"`fast_mode = {str(expected_profile.fast_mode).lower()}`."
                )
            messages.append(f"Selected profile matched: {expected_profile.key}.")

        messages.append("Structural key/profile validation passed (install Python 3.11+ or tomli for full TOML parsing).")
        return messages

    for required in ("name", "description", "developer_instructions"):
        value = data.get(required)
        if not isinstance(value, str) or not value.strip():
            raise ConfigError(f"Required custom-agent field `{required}` is missing or empty.")

    name = str(data["name"])
    validate_agent_name(name)
    if expected_name and name != expected_name:
        raise ConfigError(f"Agent name mismatch: expected {expected_name!r}, found {name!r}.")

    model = data.get("model")
    if model is not None and not isinstance(model, str):
        raise ConfigError("`model` must be a string when present.")

    effort = data.get("model_reasoning_effort")
    if effort is not None:
        if not isinstance(effort, str) or effort not in VALID_REASONING_EFFORTS:
            raise ConfigError(f"Unsupported `model_reasoning_effort`: {effort!r}.")

    service_tier = data.get("service_tier")
    if service_tier is not None and not isinstance(service_tier, str):
        raise ConfigError("`service_tier` must be a string when present.")

    features = data.get("features", {})
    if not isinstance(features, dict):
        raise ConfigError("`features` must be a TOML table when present.")
    fast_mode = features.get("fast_mode")
    if fast_mode is not None and not isinstance(fast_mode, bool):
        raise ConfigError("`features.fast_mode` must be a boolean when present.")
    if service_tier == "fast" and fast_mode is not True:
        raise ConfigError('`service_tier = "fast"` should be paired with `[features].fast_mode = true`.')

    if expected_profile:
        if model != expected_profile.model:
            raise ConfigError(
                f"Profile mismatch: expected model {expected_profile.model!r}, found {model!r}."
            )
        if effort != expected_profile.reasoning_effort:
            raise ConfigError(
                "Profile mismatch: expected reasoning effort "
                f"{expected_profile.reasoning_effort!r}, found {effort!r}."
            )
        if service_tier != expected_profile.service_tier:
            raise ConfigError(
                f"Profile mismatch: expected service tier {expected_profile.service_tier!r}, "
                f"found {service_tier!r}."
            )
        if bool(fast_mode) is not expected_profile.fast_mode:
            raise ConfigError(
                f"Profile mismatch: expected fast_mode={expected_profile.fast_mode}, found {fast_mode!r}."
            )
        messages.append(f"Selected profile matched: {expected_profile.key}.")

    messages.append("Full TOML parse passed.")
    messages.append("Required custom-agent fields passed: name, description, developer_instructions.")
    if model:
        messages.append(f"Configured model: {model}.")
    if effort:
        messages.append(f"Configured reasoning effort: {effort}.")
    if service_tier:
        messages.append(f"Configured service tier: {service_tier}.")
    else:
        messages.append("Configured service tier: standard/default.")
    return messages


def codex_version() -> tuple[str | None, str | None]:
    executable = shutil.which("codex")
    if not executable:
        return None, "Codex executable was not found on PATH."
    try:
        completed = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, f"Unable to run `codex --version`: {exc}"
    output = (completed.stdout or completed.stderr).strip()
    if completed.returncode != 0:
        return None, f"`codex --version` failed with exit code {completed.returncode}: {output}"
    return output or "Codex version command succeeded (no version text returned).", None


def run_smoke_test(agent_name: str, timeout_seconds: int) -> tuple[bool, str]:
    executable = shutil.which("codex")
    if not executable:
        return False, "Codex executable was not found on PATH."
    prompt = (
        f"Spawn the custom agent named {agent_name} and give it exactly the delegated objective SELF_CHECK. "
        "Do not inspect or modify project files. Return only the subagent result."
    )
    try:
        completed = subprocess.run(
            [executable, "--ask-for-approval", "never", prompt],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False, f"Runtime smoke test timed out after {timeout_seconds} seconds."
    except OSError as exc:
        return False, f"Unable to start Codex smoke test: {exc}"

    output = ((completed.stdout or "") + "\n" + (completed.stderr or "")).strip()
    sentinel = f"LUNA_SUBAGENT_READY:{agent_name}"
    if completed.returncode == 0 and sentinel in output:
        return True, output
    return False, output or f"Codex exited with status {completed.returncode} and returned no output."


def write_change(path: Path, before: str, after: str, dry_run: bool) -> Path | None:
    print(f"\n=== DIFF: {path} ===")
    print(unified_diff(path, before, after), end="")
    if before == after or dry_run:
        return None
    backup = backup_file(path)
    atomic_write(path, after)
    return backup


def install(args: argparse.Namespace) -> int:
    profile = PROFILES[args.profile]
    if args.dry_run and args.smoke_test:
        raise ConfigError("--smoke-test cannot be combined with --dry-run because no agent file is installed.")
    agent_name = args.agent_name or DEFAULT_AGENT_NAME_BY_PROFILE[args.profile]
    validate_agent_name(agent_name)
    project_root = detect_project_root(args.project_root)
    agent_path = resolve_agent_path(args.scope, agent_name, project_root)
    routing_path = resolve_routing_path(args.routing, project_root)

    before_agent = read_text(agent_path)
    if before_agent and MANAGED_HEADER not in before_agent and not args.force:
        raise ConfigError(
            f"Refusing to replace unmanaged agent file: {agent_path}. Inspect it first, then rerun with --force if replacement is intended."
        )
    after_agent = build_agent_toml(agent_name, profile)
    validation_messages = validate_agent_content(
        after_agent, expected_name=agent_name, expected_profile=profile
    )

    backups: list[Path] = []
    backup = write_change(agent_path, before_agent, after_agent, args.dry_run)
    if backup:
        backups.append(backup)

    if routing_path is not None:
        before_routing = read_text(routing_path)
        after_routing = upsert_marked_block(before_routing, build_routing_block(agent_name))
        backup = write_change(routing_path, before_routing, after_routing, args.dry_run)
        if backup:
            backups.append(backup)

    print("\n=== VALIDATION ===")
    for message in validation_messages:
        print(f"PASS: {message}")
    version, version_error = codex_version()
    if version:
        print(f"PASS: Installed Codex detected: {version}")
    else:
        print(f"WARN: {version_error}")
    print(f"PASS: No changes were made to {resolve_codex_home() / 'config.toml'} or unrelated agent files.")

    if args.dry_run:
        print("INFO: Dry run only; no files were written.")
    else:
        print(f"PASS: Agent file is present at {agent_path}")
        if routing_path is not None:
            print(f"PASS: Delegation routing block is present at {routing_path}")
        for path in backups:
            print(f"BACKUP: {path}")

    if args.smoke_test:
        print("\n=== OPTIONAL RUNTIME SMOKE TEST ===")
        print("INFO: This starts a real Codex turn and may consume ChatGPT credits or API tokens.")
        ok, output = run_smoke_test(agent_name, args.smoke_timeout)
        print(output)
        if not ok:
            print("FAIL: Runtime smoke test did not confirm the custom-agent sentinel.")
            return 3
        print("PASS: Runtime smoke test returned the custom-agent sentinel.")
    else:
        print(
            "INFO: Runtime discovery was not tested. Start a new Codex session and use `/agent`, "
            f"or rerun with --smoke-test, to verify that `{agent_name}` is selectable."
        )

    if profile.key == "exact":
        print(
            "NOTE: The exact profile uses both maximum reasoning and Fast mode. It follows the requested "
            "combination, but it is not the minimum-credit profile. Use --profile economy for usage-first routing."
        )
    return 0


def validate_existing(args: argparse.Namespace) -> int:
    profile = PROFILES[args.profile]
    agent_name = args.agent_name or DEFAULT_AGENT_NAME_BY_PROFILE[args.profile]
    validate_agent_name(agent_name)
    project_root = detect_project_root(args.project_root)
    agent_path = resolve_agent_path(args.scope, agent_name, project_root)
    if not agent_path.exists():
        raise ConfigError(f"Agent file does not exist: {agent_path}")

    content = read_text(agent_path)
    print(f"Validating: {agent_path}")
    for message in validate_agent_content(
        content, expected_name=agent_name, expected_profile=profile
    ):
        print(f"PASS: {message}")
    version, version_error = codex_version()
    if version:
        print(f"PASS: Installed Codex detected: {version}")
    else:
        print(f"WARN: {version_error}")

    if args.smoke_test:
        print("INFO: This starts a real Codex turn and may consume ChatGPT credits or API tokens.")
        ok, output = run_smoke_test(agent_name, args.smoke_timeout)
        print(output)
        return 0 if ok else 3

    print(
        "INFO: Static validation passed. Runtime discovery still requires a new Codex session plus `/agent`, "
        "or the optional --smoke-test."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Configure and validate a bounded GPT-5.6 Luna custom Codex agent without touching unrelated config."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument(
            "--profile",
            choices=sorted(PROFILES),
            default="exact",
            help="exact=luna/max/fast; economy=luna/medium/standard; fast-balanced=luna/medium/fast",
        )
        subparser.add_argument("--agent-name", help="Override the profile's default custom-agent name.")
        subparser.add_argument("--scope", choices=("user", "project"), default="user")
        subparser.add_argument("--project-root", help="Project root for project-scoped files; defaults to Git root or CWD.")
        subparser.add_argument(
            "--smoke-test",
            action="store_true",
            help="Start a real Codex SELF_CHECK turn; this may consume credits/tokens.",
        )
        subparser.add_argument("--smoke-timeout", type=int, default=180)

    install_parser = subparsers.add_parser("install", help="Create or update the agent and optional routing policy.")
    add_common(install_parser)
    install_parser.add_argument(
        "--routing",
        choices=("none", "global", "project"),
        default="global",
        help="Where to add the marked Sol/Luna delegation policy.",
    )
    install_parser.add_argument("--dry-run", action="store_true", help="Show diffs and validation without writing files.")
    install_parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing unmanaged target agent file after creating a backup.",
    )
    install_parser.set_defaults(func=install)

    validate_parser = subparsers.add_parser("validate", help="Validate an existing custom-agent file.")
    add_common(validate_parser)
    validate_parser.set_defaults(func=validate_existing)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except ConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("ERROR: Interrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
