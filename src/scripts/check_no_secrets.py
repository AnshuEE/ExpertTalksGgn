#!/usr/bin/env python3
"""Block hardcoded connection details and credentials in tracked files.

CLAUDE.md: "If you find yourself typing a real account identifier into a tracked
file, stop — that is the bug." This makes that a gate rather than a hope.

Placeholders (<...>, ${...}, env_var(...), os.environ, ____) are allowed — they are
how the docs and templates are supposed to refer to these values.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SELF = {"scripts/check_no_secrets.py", "tests/test_check_no_secrets.py"}

# A value is a placeholder, not a secret, if it looks like any of these.
PLACEHOLDER = re.compile(
    r"""^\s*["']?(<|\$\{|\{\{|env_var|os\.environ|\.\.\.|_{3,}|x{3,}|\*{3,})""",
    re.I,
)

RULES: list[tuple[str, re.Pattern[str], str]] = [
    (
        "snowflake account host",
        re.compile(r"[A-Za-z0-9_-]+\.snowflakecomputing\.com"),
        "use $SNOWFLAKE_ACCOUNT, not a literal account host",
    ),
    (
        "literal credential",
        re.compile(
            r"""(?ix)
            \b(password|passphrase|api_token|api_key|secret|private_key)
            \s*[:=]\s*
            (?P<value>["'][^"']{4,}["'])
            """
        ),
        "read it from an environment variable instead",
    ),
    (
        "private key block",
        re.compile(r"-----BEGIN (?:RSA |ENCRYPTED )?PRIVATE KEY-----"),
        "keys never belong in the repo; *.p8 and *.pem are gitignored",
    ),
    (
        "atlassian api token",
        re.compile(r"\bATATT[A-Za-z0-9_\-=]{20,}"),
        "tokens live in the environment, never in a tracked file",
    ),
]


def scan(text: str, path: str) -> list[str]:
    """Return one message per offending line."""
    findings = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for label, pattern, hint in RULES:
            match = pattern.search(line)
            if not match:
                continue
            value = match.groupdict().get("value") if match.groupdict() else None
            if value and PLACEHOLDER.match(value.strip("\"'")):
                continue
            findings.append(f"{path}:{lineno}: {label} — {hint}")
    return findings


def main(argv: list[str]) -> int:
    findings: list[str] = []
    for name in argv:
        path = Path(name)
        if name in SELF or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        findings.extend(scan(text, name))

    if findings:
        print("\n  Hardcoded connection details or credentials found:\n", file=sys.stderr)
        for finding in findings:
            print(f"    {finding}", file=sys.stderr)
        print("", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
