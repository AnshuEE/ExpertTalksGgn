"""Tests for the Bronze loader's read step. AAA pattern per CLAUDE.md.

Only `read_source` is covered here — it is pure pandas and needs no warehouse.
`load()` and error propagation are tested with mocks (no live warehouse needed).
"""

from unittest.mock import patch

import pandas as pd
import pytest
import snowflake.connector.errors

from src.bronze.load_online_retail import load, read_source


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


def test_load_raises_on_missing_env_var(source_xlsx):
    # Arrange — a missing env var for connection config

    # Act & Assert
    with pytest.raises(KeyError), patch.dict("os.environ", {}, clear=True):
        load(source_xlsx)


def test_load_raises_on_connection_error(source_xlsx):
    # Arrange — a connection error from Snowflake, with env vars mocked

    # Act & Assert
    env_vars = {
        "SNOWFLAKE_ACCOUNT": "test",
        "TEST_SNOWFLAKE_USER": "test",
        "TEST_SNOWFLAKE_PASSWORD": "test",
        "SNOWFLAKE_ROLE": "test",
        "SNOWFLAKE_WAREHOUSE": "test",
        "SNOWFLAKE_DATABASE": "test",
    }
    with (
        pytest.raises(snowflake.connector.errors.Error),
        patch.dict("os.environ", env_vars),
        patch("src.bronze.load_online_retail.connect") as mock_connect,
    ):
        mock_connect.side_effect = snowflake.connector.errors.ProgrammingError("Connection failed")
        load(source_xlsx)
