# AGENTS.md

> Model-agnostic. This file is the same for Claude, GPT, and Gemini. It says what the
> project **means**. `CLAUDE.md` says how work **gets done** — formatting, commit
> rules, review gates. If you're adding a rule about process, it belongs there, not here.

## Project Summary

**ExpertTalksGgn** (short name `etg`) is a three-layer Snowflake pipeline over the UCI
Online Retail dataset, built live on stage to demonstrate production-grade AI-assisted
data engineering. It serves one audience — the room at Expert Talks Gurgaon — and its
real product is not the dashboard but the *evidence* that a well-engineered harness
lets a single prompt do reliably what three supervised steps did a minute earlier.

Issue tracker project key: `ETG`. Owning team: Equal Experts — Data Engineering (Anshu
Aggarwal, Ankur Jain).

Because it is a demo, one property matters more than in a normal project: **every
shortcut is visible on a projector.** A hardcoded account identifier, an untested
model, a filter in the wrong layer — the audience sees it. Build as if reviewed live,
because it is.

## Domain vocabulary

The single highest-value section in this file. Without it, common words in this repo
are ambiguous and the model guesses.

| Word | In this repo it means | It does **not** mean |
|---|---|---|
| **model** | A dbt model — a `.sql` file in `dbt/models/` materialized as a view or table | An ML model, a Databricks model, or the LLM |
| **the model** / **LLM** | The Cortex-hosted LLM invoked via `SNOWFLAKE.CORTEX.COMPLETE()` | A dbt model |
| **layer** | Bronze, Silver, or Gold — a schema in `EXPERT_TALK` | A network or application tier |
| **raw** | The untouched Bronze table, all columns STRING | The `.xlsx` on disk (that's *the source file*) |
| **source file** | `data/raw/Online_Retail.xlsx` | A dbt `source()` |
| **staging** | Silver. Typed, deduped, flagged, still one row per source row | A pre-production environment |
| **mart** | A Gold table built for one question | Any curated table |
| **cancelled** | A row excluded from revenue by an explicit, tested Silver rule | Only "`InvoiceNo` starts with C" — see below |
| **duplicate** | Byte-identical repeat of an entire source row | A customer buying the same item twice |
| **customer** | A row with a non-null `CustomerID` | Every transacting party — ~25% of rows are guest checkouts with no ID |
| **revenue** | `Quantity × UnitPrice` over merchandise rows that survived Silver's flags | Sum of all rows |
| **product** | A `StockCode` that is actual merchandise | Every `StockCode` — postage, fees and adjustments share the column |
| **test** | A dbt schema/singular test, or a pytest test | A manual check someone ran once |
| **the harness** | `CLAUDE.md` + `AGENTS.md` + `.claude/skills/` + hooks + tests | The dbt project |

**On "cancelled" specifically.** `InvoiceNo` prefixes are a naming *convention*, not a
guarantee. Before encoding any prefix-based rule, query the distinct prefixes actually
present and their row counts. A rule that fits the rows you looked at is not the same
as a rule that fits the dataset, and the difference between those two is what this
whole session is about.

## Architecture & Dataflow

```
data/raw/Online_Retail.xlsx          the source file — 541,909 line items, never edited
        │
        │  src/bronze/load_online_retail.py   reproducible, idempotent, no cleaning
        ▼
EXPERT_TALK.BRONZE.ONLINE_RETAIL_RAW  every column STRING + 3 load-metadata columns
        │                             541,909 rows in, 541,909 rows out
        │  dbt — typing, dedup, named business rules, zero filtering
        ▼
EXPERT_TALK.SILVER.stg_online_retail  typed; flags: is_cancelled, is_return,
        │                             is_merchandise, has_customer
        │  dbt — filters using Silver's flags, never re-deriving them
        ▼
EXPERT_TALK.GOLD.fct_revenue          purpose-built, materialized as a table
        │                             dim_customer, dim_product as needed
        ▼
Streamlit-in-Snowflake                reads Gold only; deployed from the Git repository
                                      object, never `streamlit run`
```

Alongside the main flow, and feeding the Silver rules rather than the tables:

```
Bronze sample + column stats ──► SNOWFLAKE.CORTEX.COMPLETE() ──► data-quality findings
                                 (ad-hoc SQL; no semantic model,
                                  no Cortex Analyst setup)
```

**Sources.** One file, referenced by path from config — never an absolute path baked
into a script. Connection targets (account, warehouse, role, database) come from
environment variables in every layer, with no exceptions and no committed defaults.

**Project-wide defaults.** Staging materializes as `view`, marts as `table`. Schemas
are literal (`BRONZE`/`SILVER`/`GOLD`) via a `generate_schema_name` macro override.
dbt docs are regenerated as part of `dbt build`, not persisted by hand.

## Repository Structure

```
data/raw/                  the source .xlsx — read-only, never edited in place
src/bronze/                Bronze loader (Python) — the only non-dbt path to Snowflake
  load_online_retail.py    idempotent full reload
dbt/
  models/staging/          Silver — stg_online_retail.sql + schema.yml
  models/marts/            Gold — fct_revenue.sql, dim_*.sql + schema.yml
  macros/                  generate_schema_name override, shared helpers
  tests/                   singular tests for non-obvious business rules
sql/
  cortex/                  ad-hoc CORTEX.COMPLETE() profiling queries
  deploy/                  Git repository object + CREATE STREAMLIT statements
streamlit/
  app.py                   Streamlit-in-Snowflake entry point — reads Gold only
tests/                     pytest for everything outside dbt (AAA pattern)
docs/
  ai_review_checklist.md   the six checks applied to every AI-authored change
  FACILITATOR_RUNBOOK.md   run-of-show for the live session
.claude/skills/            reusable skills — create-dbt-model, and others as they earn it
```

## Feature Specifications

Feature specs live in `features/XX-feature-name/` (`XX` = zero-padded incrementing
index). Workflow:

1. Collaborate to write `PRD.md`. Wait for review.
2. On request, break the PRD into `TODO.md` — a detailed task plan in the same
   directory. Each task carries explicit acceptance criteria.

For this repo the spec is the deck plus `docs/FACILITATOR_RUNBOOK.md`; the four demo
beats are the backlog. New features during the session are out of scope by definition —
see "never expand scope without asking" in `CLAUDE.md`.

## Technical Stack & Dev Tools

Snowflake (warehouse, Cortex, Git repository objects, Streamlit-in-Snowflake), dbt Core
with the `dbt-snowflake` adapter, Python for the Bronze loader, Jira for the ticket
write-back.

- **Dependency management**: `uv` (Python 3.11). `uv venv && uv pip install -r requirements.txt`.
- **Build/test**: `python -m src.bronze.load_online_retail` for Bronze; `dbt build` for
  Silver + Gold (runs models and tests together); `pytest tests/ -v` for everything else.
- **Linters/formatters**: `ruff` (`pyproject.toml`), `sqlfluff` with the Snowflake
  dialect (`.sqlfluff`), `dbt parse` as a syntax gate. All invoked through
  `pre-commit`, so a hook catches them before a prompt has to.

Install hooks: `pre-commit install && pre-commit install --hook-type commit-msg`.

## Conventions (replicate)

- Reference internal models with `ref()` and the source file with `source()` — never a
  hardcoded `DATABASE.SCHEMA.TABLE` literal. Environment-specific values (account,
  warehouse, role, database, Jira base URL) come from env vars, always.
- Shared logic goes in `dbt/macros/` and is reused, not re-inlined. Related helpers sit
  together in one file rather than scattered.
- SQL style: lowercase keywords, leading commas, CTEs named for what they contain
  (`renamed`, `typed`, `flagged`), one CTE per transformation step. Match the file you
  are editing over the rule in this list.
- **Every model has a paired YAML entry** declaring its grain, every column, and its
  tests. A `.sql` file without a `schema.yml` entry is incomplete.
- Tests on the fields that carry business meaning: uniqueness on the declared grain,
  not-null where the data genuinely is never null (verify before asserting — ~25% of
  `CustomerID` is legitimately missing), accepted values on flags, and a singular test
  for every rule whose correctness isn't obvious from reading the SQL.

## Development Workflow

For each new feature you MUST:

1. Branch from `main`, named after the ticket (e.g. `ETG-1234-short-description` — no
   `feature/` or `fix/` prefixes).
2. Ensure pre-commit hooks are installed; commits are blocked if linting or
   commit-message checks fail.
3. Do all implementation on the feature branch, in meaningful incremental commits.
4. Run the full build + test suite before opening a PR.

During the live session, the branch-per-beat structure *is* the workflow, and the git
tag at the end of each beat is the recovery point. See the runbook.

## Commit & PR Standards

Conventional Commits **with a mandatory ticket reference**, enforced by a commit-msg
hook:

```
<type>(<scope>): ETG-<number> <description>
```

- Types: `feat|fix|docs|style|refactor|perf|test|chore|build|ci|release`. Scope optional.
- Example: `feat(silver): ETG-1234 add is_cancelled flag with prefix-coverage test`
- PR descriptions: summary + test plan, referencing the ticket. The test plan names the
  command that was actually run and the row-count delta it produced.

## Guardrails & Limitations

- **Human-in-the-loop**: PRs require review by a code owner. On stage, the human review
  moment is the demo — `docs/ai_review_checklist.md` is the checklist being applied.
- **Agents must NOT**: merge PRs, push to `main`, create or move release tags, drop or
  truncate Bronze without saying so first, alter the Git repository object or API
  integration outside `sql/deploy/`, or hand-edit lockfiles and generated dbt artifacts.
- **Never bypass safe-update patterns**: the Bronze loader replaces its own table by
  design, which is safe because Bronze is derived from a file under version control.
  Nothing else in the pipeline gets a destructive full-rebuild without being asked.
- **Data/observability**: none. This is a demo account with no monitoring, no freshness
  alerting, and no on-call. Treat every failure as one a human must notice live —
  which is exactly why the tests matter.
- **Known limitations**:
  - Auth is `externalbrowser` SSO. Sessions expire, and every connect can open a
    browser window. Never retry a failed auth in a loop.
  - Cortex model availability is region-dependent. Verify which models
    `COMPLETE()` actually serves in this account before relying on one.
  - Snowflake serves the *fetched* snapshot of the Git repository object. Code pushed
    but not fetched does not exist as far as Streamlit is concerned.
  - The source dataset's quirks are genuine and undocumented upstream. Assume anything
    you haven't queried is unknown, not clean.
