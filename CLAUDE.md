# CLAUDE.md

## What this is

A Snowflake data pipeline over the UCI Online Retail dataset (541,909 line items,
one UK gift retailer, Dec 2010 – Dec 2011), built live on stage for the Expert Talks
Gurgaon session *"Production-Ready AI for Data Engineering: Context, Trust &
Automation."*

The source file is `data/raw/Online_Retail.xlsx`. It is messy in ways that are real,
not seeded — missing customer IDs, cancellations, returns, duplicate rows, fee lines
mixed in with product lines. Handling that mess correctly, in the right layer, is the
entire point of the exercise.

Three layers, one database:

| Layer  | Schema                 | Contents                                     |
|--------|------------------------|----------------------------------------------|
| Bronze | `EXPERT_TALK.BRONZE`   | `ONLINE_RETAIL_RAW` — untouched source rows  |
| Silver | `EXPERT_TALK.SILVER`   | `stg_online_retail` — typed, deduped, ruled   |
| Gold   | `EXPERT_TALK.GOLD`     | `fct_revenue`, `dim_*` — purpose-built marts  |

A Streamlit-in-Snowflake app reads Gold and nothing else.

## Commands

Connection details come from the environment. Nothing below hardcodes an account,
warehouse, role, or credential.

```bash
# Required in every shell that touches Snowflake
export SNOWFLAKE_ACCOUNT=...        # org-account identifier
export SNOWFLAKE_USER=...           # SSO principal
export SNOWFLAKE_ROLE=...           # needs CREATE GIT REPOSITORY, CREATE STREAMLIT, CORTEX usage
export SNOWFLAKE_WAREHOUSE=...
export SNOWFLAKE_DATABASE=EXPERT_TALK
# Auth is externalbrowser SSO — no password or key env var exists. A browser
# window will open on first connect. See "SSO and long-running work" below.

# Setup
uv venv && uv pip install -r requirements.txt
pre-commit install

# Bronze
python -m src.bronze.load_online_retail          # idempotent full reload
pytest tests/ -v                                 # pytest, AAA pattern

# Silver + Gold
dbt deps
dbt build                                        # run + test, both layers
dbt build --select stg_online_retail             # one model and its tests
dbt docs generate && dbt docs serve

# Streamlit-in-Snowflake (deploy, never `streamlit run`)
snow sql -f sql/deploy/01_git_repository.sql
snow sql -f sql/deploy/02_create_streamlit.sql
```

`profiles.yml` is **gitignored**. `profiles.yml.example` is committed and reads every
value from `env_var()`. If you find yourself typing a real account identifier into a
tracked file, stop — that is the bug.

## Architecture

### Bronze — `EXPERT_TALK.BRONZE.ONLINE_RETAIL_RAW`

Bronze is a faithful copy of the source. It exists so that every later decision is
auditable against something that was never touched.

**Bronze does not clean, cast, filter, dedupe, rename, or reorder.** Specifically:

- Every source column lands as `STRING`. `Quantity` is a string. `UnitPrice` is a
  string. `InvoiceDate` is a string. `CustomerID` arrives from Excel as `17850.0` and
  is stored as the string `"17850.0"` — do not strip the `.0` here.
- No `WHERE` clause. Cancelled orders, negative quantities, blank customer IDs, and
  duplicate rows all land. 541,909 source rows in, 541,909 rows out.
- No `DISTINCT`, no `MERGE`, no dedup of any kind.
- Loaded by a re-runnable script in `src/bronze/`, not a Snowsight console upload and
  not a hand-typed `INSERT`. Someone must be able to reproduce the table from the
  file on a clean account.

Three additive metadata columns are **allowed and expected**, because they describe
the load rather than alter the data: `_LOADED_AT` (TIMESTAMP_NTZ), `_SOURCE_FILE`
(STRING), `_SOURCE_ROW` (NUMBER, the 1-based row ordinal in the sheet). Nothing else.

The loader is idempotent: a second run replaces the table's contents rather than
doubling them.

### Silver — `EXPERT_TALK.SILVER.stg_online_retail` (dbt, view)

Silver is where judgment lives. Everything Bronze refused to do happens here, and
every one of those decisions is written down.

- **Typing**: strings become `NUMBER`, `FLOAT`, `TIMESTAMP_NTZ`. Cast defensively —
  `TRY_CAST`, not `CAST` — and surface the rows that fail rather than dropping them
  silently.
- **Dedup**: the source contains exact duplicate rows. Decide what "exact" means
  here, apply it once, and record the row-count delta in the model's YAML description.
- **Business rules are named, not implied.** Any row-excluding or row-flagging rule
  gets a named column (`is_cancelled`, `is_return`, `is_merchandise`, …), a
  one-sentence description in the schema YAML explaining *the rule*, and a dbt test
  that fails if the rule stops holding.
- **Derive rules from the data, not from folklore.** A rule that matches the examples
  you happened to look at is not the same as a rule that matches the dataset. Before
  encoding one, query the warehouse for the rows it does *not* catch. `InvoiceNo`
  prefixes are the obvious trap here — check what prefixes actually occur and how many
  rows each covers before you write the predicate.

Silver keeps every row. It flags and types; it does not filter. Filtering is Gold's
job, using Silver's flags.

### Gold — `EXPERT_TALK.GOLD.fct_revenue` (dbt, table)

Gold is purpose-built for one question and materialized as tables, because a
dashboard queries it.

- `fct_revenue` answers "what did we actually sell, to whom, when." It excludes
  non-revenue rows by referencing Silver's named flags — never by re-deriving the
  rule with its own inline `LIKE 'C%'`. One rule, one definition, one place.
- Any Gold mart that filters rows carries a dbt test asserting the exclusion held —
  e.g. no negative extended revenue, no non-merchandise stock codes, no cancelled
  invoices. A mart that filters without a test proving the filter worked is not done.
- Grain is declared in the YAML description and enforced by a uniqueness test.

### Streamlit-in-Snowflake

- The app reads **only** from `EXPERT_TALK.GOLD`. Not Silver, not Bronze, not a
  hand-written CTE over raw. If the dashboard needs a number that Gold doesn't have,
  the fix is a Gold model, not a query in the app.
- Deployed from the repo through Snowflake's native Git integration, not run locally:

  ```sql
  CREATE OR REPLACE SECRET expert_talk_git_secret ...;
  CREATE OR REPLACE API INTEGRATION expert_talk_git_api ...;
  CREATE OR REPLACE GIT REPOSITORY expert_talk_repo
    API_INTEGRATION = expert_talk_git_api
    ORIGIN          = '<repo url>';
  ALTER GIT REPOSITORY expert_talk_repo FETCH;

  CREATE OR REPLACE STREAMLIT expert_talk_dashboard
    ROOT_LOCATION = '@EXPERT_TALK.PUBLIC.expert_talk_repo/branches/<branch>/streamlit'
    MAIN_FILE     = 'app.py'
    QUERY_WAREHOUSE = <warehouse>;
  ```

  The exact statements live in `sql/deploy/`. `ALTER GIT REPOSITORY ... FETCH` after
  every push — Snowflake serves the fetched snapshot, not the live remote, and a
  dashboard that "didn't update" is almost always a missing FETCH.

### Naming

| Kind             | Pattern                | Example              |
|------------------|------------------------|----------------------|
| Silver staging   | `stg_<source>`         | `stg_online_retail`  |
| Gold fact        | `fct_<subject>`        | `fct_revenue`        |
| Gold dimension   | `dim_<entity>`         | `dim_customer`       |

dbt writes to literal schemas via a `generate_schema_name` override in
`macros/generate_schema_name.sql` — without it dbt concatenates and you get
`SILVER_silver`. Adapter is `dbt-snowflake`. Staging materializes as `view`, marts as
`table`, set in `dbt_project.yml`.

## Working conventions

**Show reasoning before you write.** Before creating or altering anything in the
warehouse, in `dbt/`, or in `sql/`, say what you're about to do and why — the rule
you're encoding, the rows it affects, the alternative you rejected. One short
paragraph, before the edit, not after.

**Tests ship with the thing they test, in the same change.**
- Anything in dbt → dbt schema tests plus a singular test for any non-obvious rule.
- Anything outside dbt (the Bronze loader, helper scripts) → `pytest`, AAA pattern
  (`# Arrange` / `# Act` / `# Assert` comments present), one behaviour per test.
- "I'll add tests after" is not a plan. A model without tests is a draft.

**Never expand scope without asking.** If the task is a Silver model and you notice
Gold is wrong, say so and stop. Don't fix it in the same change. Flagging is doing
your job; silently widening the diff is not.

**Don't call it done without running it.** "Done" means the command ran, the tests
passed, and you saw the output — and you say which command you ran. If you couldn't
run it, say that instead of implying you did.

**Report row counts on every layer change.** Any change that alters row counts states
before, after, delta, and the reason. An unexplained delta is a defect, including
when the new number looks nicer.

**Push back.** If a request would put a cleaning step in Bronze, a filter in Silver, or
a business rule inside the Streamlit app, say so before doing it. Being agreeable
about a layering violation costs more later than the friction of saying no now.

### SSO and long-running work

Auth is `externalbrowser`. A browser window opens on first connect and the session can
expire mid-run — which matters most during long unattended work.

- Set `CLIENT_SESSION_KEEP_ALIVE = True` in the connection config and dbt profile.
- Establish the session *before* starting long work, not during it.
- If a connection fails with an auth error, stop and report it. Do not retry in a
  loop — each retry opens another browser window.

### Jira

The implementation comment posts via the Jira REST API through `curl`, driven by
`JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_TICKET`. A single deterministic
HTTP call needs a CLI, not an agent integration — reserve the model for the judgment
of *what to write*, not the mechanics of posting it.
