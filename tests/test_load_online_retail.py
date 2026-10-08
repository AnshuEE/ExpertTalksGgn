"""Tests for the Bronze loader. AAA pattern per CLAUDE.md.

`read_source` is pure pandas and needs no warehouse. `load()`'s warehouse round-trip
still needs a live Snowflake connection (see the `snowflake` marker), but its failure
contract — a failed load must not report a row count — is covered here with a stubbed
`connect`.
"""

import pandas as pd
import pytest
import snowflake.connector

from src.bronze import load_online_retail
from src.bronze.load_online_retail import SnowflakeConnectionConfig, read_source


@pytest.fixture
def source_xlsx(tmp_path):
    # Arrange — a tiny sheet with the messiness Bronze must NOT touch:
    # a blank CustomerID (guest checkout) and a numeric-looking one.
    path = tmp_path / "Online_Retail.xlsx"
    pd.DataFrame(
        {
            "InvoiceNo": ["536365", "536366"],
            "StockCode": ["85123A", "71053"],
            "Quantity": ["6", "-1"],
            "InvoiceDate": ["12/1/2010 8:26", "12/1/2010 8:28"],
            "UnitPrice": ["2.55", "3.39"],
            "CustomerID": ["17850", None],
            "Country": ["United Kingdom", "United Kingdom"],
        }
    ).to_excel(path, index=False)
    return path


def test_forces_every_source_column_to_string(source_xlsx):
    # Arrange — source_xlsx fixture

    # Act
    df = read_source(source_xlsx)

    # Assert
    assert df["CustomerID"].dropna().tolist() == ["17850"]
    assert df["Quantity"].tolist() == ["6", "-1"]


def test_preserves_row_count_and_blank_customer_id(source_xlsx):
    # Arrange — source_xlsx fixture has 2 rows, one with a blank CustomerID

    # Act
    df = read_source(source_xlsx)

    # Assert
    assert len(df) == 2
    assert df["CustomerID"].isna().sum() == 1


def test_adds_sequential_source_row_starting_at_one(source_xlsx):
    # Arrange — source_xlsx fixture

    # Act
    df = read_source(source_xlsx)

    # Assert
    assert df["_SOURCE_ROW"].tolist() == [1, 2]


def test_adds_source_file_and_loaded_at_metadata(source_xlsx):
    # Arrange — source_xlsx fixture

    # Act
    df = read_source(source_xlsx)

    # Assert
    assert (df["_SOURCE_FILE"] == str(source_xlsx)).all()
    assert df["_LOADED_AT"].notna().all()


@pytest.fixture
def snowflake_env(monkeypatch):
    # Arrange — the env vars load() reads, so the test exercises the load path
    # rather than failing on a missing variable.
    for name in (
        "SNOWFLAKE_ACCOUNT",
        "TEST_SNOWFLAKE_USER",
        "TEST_SNOWFLAKE_PASSWORD",
        "SNOWFLAKE_ROLE",
        "SNOWFLAKE_WAREHOUSE",
        "SNOWFLAKE_DATABASE",
    ):
        monkeypatch.setenv(name, "stub")


class _StubConnection:
    """Minimal stand-in for SnowflakeConnection: context manager + cursor()."""

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def cursor(self):
        return self

    def execute(self, sql):
        return self


def test_load_raises_when_the_warehouse_load_fails(source_xlsx, snowflake_env, monkeypatch):
    # Arrange — connect() fails the way a bad credential or dead warehouse would
    def fail(config):
        raise snowflake.connector.errors.DatabaseError("connection refused")

    monkeypatch.setattr(load_online_retail, "connect", fail)

    # Act / Assert — the failure propagates; it is not downgraded to a row count
    with pytest.raises(snowflake.connector.errors.DatabaseError):
        load_online_retail.load(source_xlsx)


def test_load_returns_row_count_when_the_write_succeeds(source_xlsx, snowflake_env, monkeypatch):
    # Arrange — a connection and write that both succeed
    monkeypatch.setattr(load_online_retail, "connect", lambda config: _StubConnection())
    monkeypatch.setattr(
        load_online_retail, "write_pandas", lambda conn, df, **kwargs: (True, 1, len(df), [])
    )

    # Act
    rows = load_online_retail.load(source_xlsx)

    # Assert — the fixture sheet has 2 rows
    assert rows == 2


def test_connection_config_reads_every_field_from_the_environment(monkeypatch):
    # Arrange — a distinct value per variable so a mis-wired field is visible
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "acct")
    monkeypatch.setenv("TEST_SNOWFLAKE_USER", "usr")
    monkeypatch.setenv("TEST_SNOWFLAKE_PASSWORD", "pwd")
    monkeypatch.setenv("SNOWFLAKE_ROLE", "rol")
    monkeypatch.setenv("SNOWFLAKE_WAREHOUSE", "whs")
    monkeypatch.setenv("SNOWFLAKE_DATABASE", "dbs")

    # Act
    config = SnowflakeConnectionConfig.from_env()

    # Assert
    assert config == SnowflakeConnectionConfig(
        account="acct",
        user="usr",
        password="pwd",
        role="rol",
        warehouse="whs",
        database="dbs",
    )


def test_connection_config_raises_when_an_environment_variable_is_missing(monkeypatch):
    # Arrange — every variable present except the account
    monkeypatch.delenv("SNOWFLAKE_ACCOUNT", raising=False)
    monkeypatch.setenv("TEST_SNOWFLAKE_USER", "usr")
    monkeypatch.setenv("TEST_SNOWFLAKE_PASSWORD", "pwd")
    monkeypatch.setenv("SNOWFLAKE_ROLE", "rol")
    monkeypatch.setenv("SNOWFLAKE_WAREHOUSE", "whs")
    monkeypatch.setenv("SNOWFLAKE_DATABASE", "dbs")

    # Act / Assert — a missing variable fails loudly rather than defaulting
    with pytest.raises(KeyError):
        SnowflakeConnectionConfig.from_env()
