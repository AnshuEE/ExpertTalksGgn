"""Tests for the Bronze loader's read step. AAA pattern per CLAUDE.md.

Only `read_source` is covered here — it is pure pandas and needs no warehouse.
`load()` is a thin wrapper around `write_pandas` and would only be meaningfully
tested against a live Snowflake connection (see the `snowflake` marker).
"""

import pandas as pd
import pytest

from src.bronze.load_online_retail import read_source


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
