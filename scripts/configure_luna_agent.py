#!/usr/bin/env python3
"""Safe entry point for configuring and briefing a bounded Luna subagent."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from luna_delegation import *  # noqa: F401,F403,E402
from luna_delegation.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
