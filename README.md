# Production-Ready AI for Data Engineering

Companion repo for the Expert Talks Gurgaon session *"Production-Ready AI for Data
Engineering: Context, Trust & Automation"* — Anshu Aggarwal & Ankur Jain, Equal Experts.

A three-layer **Snowflake** pipeline over the UCI Online Retail dataset, built live on
stage using **dbt Core** and an AI agent. The pipeline is the vehicle. The point is
what surrounds it.

---

## The argument

> AI bridges engineering gaps. Exceptional data engineering fills them.

The bottleneck in production GenAI is not model capability — it's trust, context, and
engineering discipline. This repo demonstrates that with a deliberately unfair
comparison:

- **Beats 2–3** — an agent builds ingestion and profiling under human supervision.
  It gets corrected three times, and each correction is a real defect a reviewer had
  to catch.
- **Beat 4** — a new branch, the supervised work thrown away, and **one prompt** builds
  the whole pipeline end to end, unattended.

Same model. Same data. The only difference is that the three corrections had already
been written down — in `CLAUDE.md`, `AGENTS.md`, and a skill file — *before* anything
touched the warehouse.

That's the harness, and it's the actual deliverable here.

## What's in the harness

| File | Role |
|---|---|
| [`AGENTS.md`](AGENTS.md) | **What the project means.** Model-agnostic — works with Claude, GPT, or Gemini. Domain vocabulary, dataflow, conventions. |
| [`CLAUDE.md`](CLAUDE.md) | **How work gets done.** Layer rules, commands, review gates, testing standard. |
| [`.claude/skills/create-dbt-model/`](.claude/skills/create-dbt-model/SKILL.md) | A reusable workflow for scaffolding a Silver or Gold model with its YAML and tests as one unit. |
| [`docs/ai_review_checklist.md`](docs/ai_review_checklist.md) | Six checks applied to every AI-authored change. |
| [`docs/FACILITATOR_RUNBOOK.md`](docs/FACILITATOR_RUNBOOK.md) | Run-of-show, exact prompts, risk register, fallback artifacts. |
| `.pre-commit-config.yaml` + `scripts/` | The gates. Linting, tests, commit-message convention, and a hardcoded-credential scanner. |

Start with `AGENTS.md` → the **domain vocabulary table**. It's the highest-leverage
thing in the repo: about a hundred words that stop a model guessing what "model" means.

## Architecture

```
data/raw/Online_Retail.xlsx          541,909 line items, one UK gift retailer, Dec 2010 – Dec 2011
        │
        │  src/bronze/  ·  Python, reproducible, idempotent
        ▼
EXPERT_TALK.BRONZE.ONLINE_RETAIL_RAW  every column STRING. No cleaning, casting,
        │                             filtering, or dedup. 541,909 in → 541,909 out.
        │  dbt Core  ·  typing, dedup, named business rules
        ▼
EXPERT_TALK.SILVER.stg_online_retail  typed; flags is_cancelled / is_return /
        │                             is_merchandise / has_customer. Flags, never filters.
        │  dbt Core  ·  filters using Silver's flags
        ▼
EXPERT_TALK.GOLD.fct_revenue          purpose-built, materialized as tables
        ▼
Streamlit-in-Snowflake                reads Gold only; deployed via the Snowflake
                                      Git repository object, never `streamlit run`
```

Alongside it, feeding the Silver rules rather than the tables:

```
Bronze sample + column stats ──► SNOWFLAKE.CORTEX.COMPLETE() ──► data-quality findings
```

No semantic model, no Cortex Analyst setup — just a SQL function in a worksheet.

## Why this dataset

Because it's genuinely messy, and none of it is seeded:

| Issue | Scale |
|---|---|
| Missing `CustomerID` (guest checkouts — valid, not errors) | 135,080 rows (24.9%) |
| Cancelled orders, `InvoiceNo` starts `C` | 9,288 rows, −£896,812 |
| Negative / zero `Quantity` | 10,624 rows |
| Negative / zero `UnitPrice` | 2,517 rows |
| Exact duplicate rows | 5,268 rows |
| Non-merchandise `StockCode`s (`POST`, `DOT`, `BANK CHARGES`, `AMAZONFEE`, gift cards…) | ~33 codes |
| Case-inconsistent `StockCode` (`15056BL` vs `15056bl`) | 117 codes |
| **`A`-prefix "Adjust bad debt" rows** | **3 rows, net −£11,062.06** |

That last row is the one worth your attention. Everyone filters cancellations with
`where invoice_no not like 'C%'`. Three rows use an `A` prefix instead — and they're
arranged one positive, two negative, so a naive filter leaves a total that looks
*almost* right. A pattern that fits the rows you looked at is not a rule.

## Quickstart

Requires Python 3.11+, [uv](https://docs.astral.sh/uv/), and a Snowflake account with
Cortex enabled.

```bash
git clone git@github.com:AnshuEE/ExpertTalksGgn.git
cd ExpertTalksGgn

uv venv && uv pip install -r requirements.txt
pre-commit install                       # installs both pre-commit and commit-msg hooks

# The 23MB source file is not committed — fetch it
mkdir -p data/raw && curl -sSL -o /tmp/or.zip \
  "https://archive.ics.uci.edu/static/public/352/online+retail.zip" \
  && unzip -p /tmp/or.zip "Online Retail.xlsx" > data/raw/Online_Retail.xlsx

cp dbt/profiles.yml.example dbt/profiles.yml     # gitignored; reads env vars only
```

Then export your connection details — **nothing is ever hardcoded in a tracked file**:

```bash
export SNOWFLAKE_ACCOUNT=...     SNOWFLAKE_USER=...
export SNOWFLAKE_ROLE=...        SNOWFLAKE_WAREHOUSE=...
export SNOWFLAKE_DATABASE=EXPERT_TALK
```

Provision the warehouse objects and the Git integration:

```bash
snow sql -f sql/deploy/01_git_repository.sql     # fill in the <placeholders> first
```

## Commands

All dbt commands are **dbt Core CLI**. There is no dbt Cloud in this project.

```bash
# Bronze
python -m src.bronze.load_online_retail    # idempotent full reload
pytest tests/ -v                           # pytest, AAA pattern

# Silver + Gold — dbt Core
dbt deps                        --project-dir dbt --profiles-dir dbt
dbt build                       --project-dir dbt --profiles-dir dbt
dbt build --select stg_online_retail --project-dir dbt --profiles-dir dbt
dbt docs generate               --project-dir dbt --profiles-dir dbt

# Dashboard
snow sql -f sql/deploy/02_create_streamlit.sql
```

`dbt build` runs models **and** their tests together — that pairing is deliberate and
enforced by the `create-dbt-model` skill.

## Authentication

Two dbt targets, because they have genuinely different constraints:

| Target | Auth | Used by |
|---|---|---|
| `dev` (default) | `externalbrowser` SSO | Humans, laptops, the live demo |
| `ci` | Key-pair (RSA) | GitHub Actions — **CI has no browser, so SSO cannot work there** |

CI's warehouse job is opt-in and builds into a separate `EXPERT_TALK_CI` database so it
can never touch the demo objects. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Repo map

```
AGENTS.md CLAUDE.md          the harness — read these first
.claude/skills/              reusable agent workflows
docs/                        review checklist + facilitator runbook
src/bronze/                  Bronze loader (built live)
dbt/
  models/staging/            Silver (built live)
  models/marts/              Gold (built live)
  macros/                    generate_schema_name override — literal BRONZE/SILVER/GOLD
sql/cortex/                  ad-hoc CORTEX.COMPLETE() profiling (built live)
sql/deploy/                  Git repository object + CREATE STREAMLIT
streamlit/                   Streamlit-in-Snowflake app (built live)
scripts/                     pre-commit gates
tests/                       pytest, AAA pattern
```

Directories marked *built live* are empty by design — they get created on stage. That's
the demo.

## Conventions

Conventional Commits with a mandatory ticket reference, enforced by a `commit-msg` hook:

```
<type>(<scope>): ETG-<number> <description>
feat(silver): ETG-1234 add is_cancelled flag with prefix-coverage test
```

Branches are named for the ticket — `ETG-1234-short-description`, no `feature/` prefix.

## Credits

Dataset: [UCI Machine Learning Repository — Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail)
(Daqing Chen, 2015). Licensed CC BY 4.0.
