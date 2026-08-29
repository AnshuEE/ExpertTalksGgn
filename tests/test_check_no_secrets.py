"""Tests for the hardcoded-credential gate. AAA pattern per CLAUDE.md."""

import pytest

from scripts.check_no_secrets import scan


@pytest.mark.parametrize(
    "line",
    [
        'account: "xy12345.eu-west-1.snowflakecomputing.com"',
        "password = 'hunter2000'",
        'private_key: "MIIEvQIBADANBgkq"',
        "-----BEGIN PRIVATE KEY-----",
        "jira_api_token = 'ATATT3xFfGF0aBcDeFgHiJkLmNoPqRsTuV'",
    ],
)
def test_flags_hardcoded_values(line):
    # Arrange — line supplied by parametrize

    # Act
    findings = scan(line, "some_file.py")

    # Assert
    assert len(findings) == 1


@pytest.mark.parametrize(
    "line",
    [
        "account: \"{{ env_var('SNOWFLAKE_ACCOUNT') }}\"",
        'password: "${SNOWFLAKE_PASSWORD}"',
        'api_token: "<your token here>"',
        "secret = os.environ['JIRA_API_TOKEN']",
        "| `SNOWFLAKE_ACCOUNT` | `________` | org-account identifier |",
        "export SNOWFLAKE_ACCOUNT=...",
        "authenticator: externalbrowser",
    ],
)
def test_allows_placeholders_and_env_lookups(line):
    # Arrange — line supplied by parametrize

    # Act
    findings = scan(line, "docs/FACILITATOR_RUNBOOK.md")

    # Assert
    assert findings == []


def test_reports_file_and_line_number():
    # Arrange
    text = "ok line\nok line\npassword = 'literalvalue'\n"

    # Act
    findings = scan(text, "src/loader.py")

    # Assert
    assert findings == [
        "src/loader.py:3: literal credential — read it from an environment variable instead"
    ]
