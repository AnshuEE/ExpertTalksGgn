"""Idempotent Bronze loader — data/raw/Online_Retail.xlsx -> BRONZE.ONLINE_RETAIL_RAW.

CLAUDE.md: Bronze is a faithful copy of the source. No cleaning, casting, filtering,
dedup, or reorder happens here — that judgment lives in Silver. Every column is read
with dtype=str so pandas never infers CustomerID as float64 (which would silently
turn "17850" into "17850.0" before anyone chose that).
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

SOURCE_FILE = Path("data/raw/Online_Retail.xlsx")
SCHEMA = "BRONZE"
TABLE_NAME = "ONLINE_RETAIL_RAW"

# Explicit DDL, not auto_create_table: write_pandas's dtype inference maps the
# _LOADED_AT datetime64 column to NUMBER (raw epoch int), not TIMESTAMP_NTZ, on
# this connector/pyarrow combination. Every source column is varchar per CLAUDE.md
# ("every column lands as STRING") — only the three metadata columns get a real type.
CREATE_TABLE_SQL = f"""
create or replace table {SCHEMA}.{TABLE_NAME} (
    invoiceno     varchar,
    stockcode     varchar,
    description   varchar,
    quantity      varchar,
    invoicedate   varchar,
    unitprice     varchar,
    customerid    varchar,
    country       varchar,
    _source_row   number,
    _source_file  varchar,
    _loaded_at    timestamp_ntz
)
"""


def read_source(path: Path = SOURCE_FILE) -> pd.DataFrame:
    """Read the source file with every column forced to string, no other changes."""
    df = pd.read_excel(path, dtype=str)
    df.insert(0, "_SOURCE_ROW", range(1, len(df) + 1))
    df["_SOURCE_FILE"] = str(path)
    # ISO string, not a native datetime: write_pandas round-trips datetime64
    # through Arrow/Parquet with an epoch-scale bug that corrupts the value
    # even into a correctly-typed TIMESTAMP_NTZ column. A string is cast on
    # load like every other Bronze column, with no scale ambiguity.
    df["_LOADED_AT"] = datetime.now(UTC).replace(tzinfo=None).isoformat(sep=" ")
    return df


def connect() -> snowflake.connector.SnowflakeConnection:
    # This account has no SAML IdP configured, so externalbrowser SSO fails at
    # auth — use password auth instead, with every parameter passed explicitly
    # (mixing connection_name with override kwargs silently drops database/warehouse).
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["TEST_SNOWFLAKE_USER"],
        password=os.environ["TEST_SNOWFLAKE_PASSWORD"],
        role=os.environ["SNOWFLAKE_ROLE"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        schema=SCHEMA,
        client_session_keep_alive=True,
    )


def load(path: Path = SOURCE_FILE) -> int:
    """Full idempotent reload of BRONZE.ONLINE_RETAIL_RAW. Returns rows loaded."""
    df = read_source(path)
    with connect() as conn:
        conn.cursor().execute(CREATE_TABLE_SQL)
        write_pandas(
            conn,
            df,
            table_name=TABLE_NAME,
            quote_identifiers=False,
        )
    return len(df)


def main() -> int:
    rows = load()
    print(f"Loaded {rows} rows into {SCHEMA}.{TABLE_NAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
