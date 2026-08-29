"""Tests for the commit-message gate.

The harness enforces a standard; this proves the enforcement actually works.
AAA pattern per CLAUDE.md.
"""

import pytest

from scripts.check_commit_msg import is_valid


@pytest.mark.parametrize(
    "message",
    [
        "feat(silver): ETG-1234 add is_cancelled flag",
        "fix: ETG-7 correct row-count assertion",
        "chore(harness): ETG-1234 add context files and dbt model skill",
        "refactor(gold)!: ETG-99 change fct_revenue grain",
        "docs: ETG-1234 first line\n\nA longer body follows.",
        "Merge branch 'main' into ETG-1234-one-shot-pipeline",
        'Revert "feat(silver): ETG-1234 add is_cancelled flag"',
    ],
)
def test_accepts_conforming_messages(message):
    # Arrange — message supplied by parametrize

    # Act
    result = is_valid(message)

    # Assert
    assert result is True


@pytest.mark.parametrize(
    ("message", "why"),
    [
        ("feat: AI harness", "no ticket reference"),
        ("ETG-1234 add a thing", "no conventional-commit type"),
        ("feat(silver) ETG-1234 add a flag", "missing colon"),
        ("feat: etg-1234 add a flag", "ticket key must be uppercase"),
        ("feat: ETG-1234", "no description after the ticket"),
        ("wip: ETG-1234 halfway through", "'wip' is not an allowed type"),
        ("feat: JIRA-1234 wrong project key", "wrong project key"),
        ("", "empty message"),
        ("# only a comment line", "comments are skipped, leaving nothing"),
    ],
)
def test_rejects_nonconforming_messages(message, why):
    # Arrange — message supplied by parametrize

    # Act
    result = is_valid(message)

    # Assert
    assert result is False, f"should have been rejected: {why}"
