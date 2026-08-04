"""Safe filesystem and path operations for Luna configuration."""

from __future__ import annotations

import difflib
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .model import ROUTING_END, ROUTING_START, ConfigError


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
    stamp = utc_stamp()
    candidate = path.with_name(f"{path.name}.bak.{stamp}")
    counter = 1
    while candidate.exists():
        candidate = path.with_name(f"{path.name}.bak.{stamp}.{counter}")
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
    rendered = "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"{path} (before)",
            tofile=f"{path} (after)",
        )
    )
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
