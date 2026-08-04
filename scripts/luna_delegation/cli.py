"""Argument parser and main entry point for the Luna helper."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from .model import PROFILES, ConfigError
from .runtime import install, print_contract, validate_existing


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Configure, validate, and brief a bounded GPT-5.6 Luna custom Codex agent."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_agent_selection(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument(
            "--profile",
            choices=sorted(PROFILES),
            default="exact",
            help="exact=luna/max/fast; economy=luna/medium/standard; fast-balanced=luna/medium/fast",
        )
        subparser.add_argument("--agent-name", help="Override the profile's default agent name.")

    def add_common(subparser: argparse.ArgumentParser) -> None:
        add_agent_selection(subparser)
        subparser.add_argument("--scope", choices=("user", "project"), default="user")
        subparser.add_argument("--project-root", help="Project root; defaults to Git root or CWD.")
        subparser.add_argument("--smoke-test", action="store_true")
        subparser.add_argument("--smoke-timeout", type=int, default=180)

    install_parser = subparsers.add_parser("install", help="Create or update agent and routing.")
    add_common(install_parser)
    install_parser.add_argument(
        "--routing", choices=("none", "global", "project"), default="global"
    )
    install_parser.add_argument("--dry-run", action="store_true")
    install_parser.add_argument("--force", action="store_true")
    install_parser.set_defaults(func=install)

    validate_parser = subparsers.add_parser("validate", help="Validate an existing agent file.")
    add_common(validate_parser)
    validate_parser.set_defaults(func=validate_existing)

    contract_parser = subparsers.add_parser("contract", help="Print a delegation contract.")
    add_agent_selection(contract_parser)
    contract_parser.set_defaults(func=print_contract)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except ConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("ERROR: Interrupted.", file=sys.stderr)
        return 130
