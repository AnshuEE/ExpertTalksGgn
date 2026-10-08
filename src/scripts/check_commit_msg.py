#!/usr/bin/env python3
"""Enforce Conventional Commits with a mandatory ticket reference.

Format:  <type>(<scope>): ETG-<number> <description>
Example: feat(silver): ETG-1234 add is_cancelled flag with prefix-coverage test

Wired in as a pre-commit `commit-msg` hook. See CLAUDE.md / AGENTS.md.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TYPES = (
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "chore",
    "build",
    "ci",
    "release",
)

PATTERN = re.compile(
    rf"^(?:{'|'.join(TYPES)})"  # type
    r"(?:\([a-z0-9._-]+\))?"  # optional (scope)
    r"!?: "  # optional breaking-change !, then ": "
    r"ETG-\d+ "  # mandatory ticket
    r"\S.*$"  # non-empty description
)

# Commits git generates itself, which must not be blocked.
EXEMPT = re.compile(r"^(Merge |Revert |fixup! |squash! )")


def is_valid(message: str) -> bool:
    """True if the first non-comment line satisfies the convention."""
    for line in message.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        return bool(EXEMPT.match(stripped) or PATTERN.match(stripped))
    return False


def main() -> int:
    if len(sys.argv) < 2:
        print("check_commit_msg.py: expected a commit message file path", file=sys.stderr)
        return 2

    message = Path(sys.argv[1]).read_text(encoding="utf-8")
    if is_valid(message):
        return 0

    subject = next(
        (ln for ln in message.splitlines() if ln.strip() and not ln.startswith("#")),
        "<empty>",
    )
    print(
        "\n  Commit message rejected.\n"
        f"    got:      {subject}\n"
        "    expected: <type>(<scope>): ETG-<number> <description>\n"
        "    example:  feat(silver): ETG-1234 add is_cancelled flag\n"
        f"    types:    {', '.join(TYPES)}\n",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
