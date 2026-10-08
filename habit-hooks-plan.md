# habit-hooks fix plan — src/bronze/load_online_retail.py

Three findings from `habit-hooks --all`. Each below: what's wrong, the root cause,
the fix, and how to verify it.

## 1. swallowed-exception — line 96

**Current code:**
```python
try:
    conn = connect(...)
    with conn:
        conn.cursor().execute(CREATE_TABLE_SQL)
        write_pandas(conn, df, table_name=TABLE_NAME, quote_identifiers=False)
except Exception as exc:
    print(f"Warning: load failed: {exc}")
return len(df)
```

**Why this is a real bug, not just style:** `load()` returns `len(df)` unconditionally,
even when the `except` fires. `main()` then prints `"Loaded {rows} rows"` — a failed
load reports success. Combined with "idempotent full reload" in CLAUDE.md, a silent
failure here means the Bronze table can go stale with nobody told.

**Fix:**
- Remove the broad `except Exception`. There is no recovery available at this call
  site — a connection or load failure should stop the run, not be downgraded to a
  printed warning.
- Let `snowflake.connector.errors.Error` (base class covering auth, DDL, and
  `write_pandas` upload failures) propagate. Don't catch `KeyError` from the
  `os.environ[...]` lookups either — a missing env var should also fail loudly, which
  it already does today once the `except Exception` is gone.
- Drop the `try` block entirely:
  ```python
  def load(path: Path = SOURCE_FILE) -> int:
      df = read_source(path)
      conn = connect(
          account=os.environ["SNOWFLAKE_ACCOUNT"],
          user=os.environ["TEST_SNOWFLAKE_USER"],
          password=os.environ["TEST_SNOWFLAKE_PASSWORD"],
          role=os.environ["SNOWFLAKE_ROLE"],
          warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
          database=os.environ["SNOWFLAKE_DATABASE"],
      )
      with conn:
          conn.cursor().execute(CREATE_TABLE_SQL)
          write_pandas(conn, df, table_name=TABLE_NAME, quote_identifiers=False)
      return len(df)
  ```

**Verify:** `pytest tests/ -v` — add/confirm a test that a connection or execute
failure raises out of `load()` rather than returning a row count.

## 2. too-many-parameters — line 58 (`connect`)

**Current signature:**
```python
def connect(
    account: str,
    user: str,
    password: str,
    role: str,
    warehouse: str,
    database: str,
) -> snowflake.connector.SnowflakeConnection:
```

**Missing abstraction:** these six values always travel together — they're read
together from `os.environ` in `load()` and passed together into `connect()`. That's
a connection profile, and the project already has a name for it: `profiles.yml` /
`profiles.yml.example` (dbt side) describes exactly this set of fields read via
`env_var()`. Introduce the equivalent on the Python side as a small dataclass.

**Fix:**
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class SnowflakeConnectionConfig:
    account: str
    user: str
    password: str
    role: str
    warehouse: str
    database: str

    @classmethod
    def from_env(cls) -> "SnowflakeConnectionConfig":
        return cls(
            account=os.environ["SNOWFLAKE_ACCOUNT"],
            user=os.environ["TEST_SNOWFLAKE_USER"],
            password=os.environ["TEST_SNOWFLAKE_PASSWORD"],
            role=os.environ["SNOWFLAKE_ROLE"],
            warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
            database=os.environ["SNOWFLAKE_DATABASE"],
        )


def connect(config: SnowflakeConnectionConfig) -> snowflake.connector.SnowflakeConnection:
    return snowflake.connector.connect(
        account=config.account,
        user=config.user,
        password=config.password,
        role=config.role,
        warehouse=config.warehouse,
        database=config.database,
        schema=SCHEMA,
        client_session_keep_alive=True,
    )
```

Call site in `load()` becomes `connect(SnowflakeConnectionConfig.from_env())` — the
env var reads move out of `load()` entirely, so `load()` no longer needs to know the
individual variable names.

**Verify:** `pytest tests/ -v` — existing tests that call `connect(...)` with
positional/keyword args need updating to construct a `SnowflakeConnectionConfig`
first. Check `tests/` for current `connect()` call sites before editing.

## 3. unused-import — line 11

**Current code:** `import json` — nothing in the module references `json`.

**Fix:** delete the import line. No side effects depend on it (it's not imported for
side effects, and nothing re-exports it).

**Verify:** `python -m py_compile src/bronze/load_online_retail.py` and
`pytest tests/ -v` to confirm nothing was relying on it transitively.

## Order of operations

Fix #3 first (trivial, zero risk), then #1 (behavior change, needs a test), then #2
(signature change, touches call sites in `load()` and in `tests/`). Run the full
`pytest tests/ -v` suite after each step, not just at the end — these three changes
touch the same file and can mask each other's regressions.

## Out of scope — flagged, not fixed here

`connect()` authenticates with `password=os.environ["TEST_SNOWFLAKE_PASSWORD"]` and a
comment claiming "this account has no SAML IdP configured." CLAUDE.md's Commands
section specifies `externalbrowser` SSO with no password env var in the connection
config. This is a layering/auth discrepancy unrelated to the three findings above —
raising it per CLAUDE.md's "push back" convention, not changing it as part of this
plan.
