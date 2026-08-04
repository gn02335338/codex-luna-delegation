"""Runtime commands for installing, validating, and briefing Luna."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from .model import (
    DEFAULT_AGENT_NAME_BY_PROFILE,
    MANAGED_HEADER,
    PROFILES,
    ConfigError,
    build_agent_toml,
    build_delegation_contract,
    build_routing_block,
    validate_agent_name,
)
from .storage import (
    atomic_write,
    backup_file,
    detect_project_root,
    read_text,
    resolve_agent_path,
    resolve_codex_home,
    resolve_routing_path,
    unified_diff,
    upsert_marked_block,
)
from .validation import validate_agent_content


def codex_version() -> tuple[str | None, str | None]:
    executable = shutil.which("codex")
    if not executable:
        return None, "Codex executable was not found on PATH."
    try:
        completed = subprocess.run(
            [executable, "--version"], capture_output=True, text=True, timeout=15, check=False
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


def selected_agent_name(args: argparse.Namespace) -> str:
    agent_name = args.agent_name or DEFAULT_AGENT_NAME_BY_PROFILE[args.profile]
    validate_agent_name(agent_name)
    return agent_name


def install(args: argparse.Namespace) -> int:
    profile = PROFILES[args.profile]
    if args.dry_run and args.smoke_test:
        raise ConfigError("--smoke-test cannot be combined with --dry-run.")
    agent_name = selected_agent_name(args)
    project_root = detect_project_root(args.project_root)
    agent_path = resolve_agent_path(args.scope, agent_name, project_root)
    routing_path = resolve_routing_path(args.routing, project_root)

    before_agent = read_text(agent_path)
    if before_agent and MANAGED_HEADER not in before_agent and not args.force:
        raise ConfigError(
            f"Refusing to replace unmanaged agent file: {agent_path}. Inspect it, then use --force if intended."
        )
    after_agent = build_agent_toml(agent_name, profile)
    validation = validate_agent_content(after_agent, agent_name, profile)

    backups: list[Path] = []
    backup = write_change(agent_path, before_agent, after_agent, args.dry_run)
    if backup:
        backups.append(backup)
    if routing_path is not None:
        before = read_text(routing_path)
        after = upsert_marked_block(before, build_routing_block(agent_name))
        backup = write_change(routing_path, before, after, args.dry_run)
        if backup:
            backups.append(backup)

    print("\n=== VALIDATION ===")
    for message in validation:
        print(f"PASS: {message}")
    version, error = codex_version()
    print(f"PASS: Installed Codex detected: {version}" if version else f"WARN: {error}")
    print(f"PASS: No changes were made to {resolve_codex_home() / 'config.toml'} or unrelated agents.")
    if args.dry_run:
        print("INFO: Dry run only; no files were written.")
    else:
        print(f"PASS: Agent file is present at {agent_path}")
        if routing_path is not None:
            print(f"PASS: Delegation routing block is present at {routing_path}")
        for path in backups:
            print(f"BACKUP: {path}")

    if args.smoke_test:
        print("INFO: This starts a real Codex turn and may consume credits or API tokens.")
        ok, output = run_smoke_test(agent_name, args.smoke_timeout)
        print(output)
        if not ok:
            print("FAIL: Runtime smoke test did not confirm the sentinel.")
            return 3
        print("PASS: Runtime smoke test returned the custom-agent sentinel.")
    else:
        print(
            "INFO: Runtime discovery was not tested. Start a new Codex session and use `/agent`, "
            f"or rerun with --smoke-test, to verify `{agent_name}`."
        )
    if profile.key == "exact":
        print(
            "NOTE: The exact profile uses maximum reasoning and Fast mode. GPT-5.6 Fast mode "
            "consumes ChatGPT credits at 2.5x Standard; use --profile economy for usage-first routing."
        )
    return 0


def validate_existing(args: argparse.Namespace) -> int:
    profile = PROFILES[args.profile]
    agent_name = selected_agent_name(args)
    project_root = detect_project_root(args.project_root)
    agent_path = resolve_agent_path(args.scope, agent_name, project_root)
    if not agent_path.exists():
        raise ConfigError(f"Agent file does not exist: {agent_path}")
    print(f"Validating: {agent_path}")
    for message in validate_agent_content(read_text(agent_path), agent_name, profile):
        print(f"PASS: {message}")
    version, error = codex_version()
    print(f"PASS: Installed Codex detected: {version}" if version else f"WARN: {error}")
    if args.smoke_test:
        print("INFO: This starts a real Codex turn and may consume credits or API tokens.")
        ok, output = run_smoke_test(agent_name, args.smoke_timeout)
        print(output)
        return 0 if ok else 3
    print("INFO: Static validation passed; runtime discovery still requires `/agent` or --smoke-test.")
    return 0


def print_contract(args: argparse.Namespace) -> int:
    print(build_delegation_contract(selected_agent_name(args)), end="")
    return 0
