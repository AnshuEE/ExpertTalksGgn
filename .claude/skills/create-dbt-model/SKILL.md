---
name: create-dbt-model
description: Scaffold a new Silver (staging) or Gold (mart) dbt model for the Snowflake Online Retail pipeline — SQL file, schema.yml entry, and tests together, following this project's layer rules. Use whenever a new dbt model, staging model, fact, dimension, or mart is requested, or when an existing model needs its paired YAML and tests brought up to standard.
---

# Create a dbt model

Scaffolds a model **and** its documentation **and** its tests as one unit. A `.sql`
file alone is not a deliverable here — a model without a `schema.yml` entry and tests
is a draft, and this skill exists so that never happens by accident.

Read `CLAUDE.md` (layer rules) and `AGENTS.md` (domain vocabulary) before starting.
This skill assumes both.

## Step 1 — Establish which layer, and say so

| | Silver (staging) | Gold (mart) |
|---|---|---|
| Path | `dbt/models/staging/` | `dbt/models/marts/` |
| Name | `stg_<source>` | `fct_<subject>` / `dim_<entity>` |
| Materialization | `view` | `table` |
| Reads from | `source()` | `ref()` on Silver or Gold |
| Filters rows? | **No** | Yes — using Silver's flags |
| Job | Type, dedup, flag | Aggregate, join, shape for one question |

If the request is ambiguous about the layer, ask. Do not pick one and proceed — the
layer determines whether filtering is correct or a violation.

State in one paragraph, **before writing any file**: the layer, the grain, the rows
affected, and any rule you're about to encode. This is the `CLAUDE.md` "show reasoning
before you write" convention, and it is the moment a reviewer can cheaply stop you.

## Step 2 — Interrogate the data before encoding a rule

Any rule that excludes or flags rows must be derived from the warehouse, not assumed.
Run the query, read the result, then write the predicate.

```sql
-- What values actually occur, and how much of the table does each cover?
select
    <the expression your rule keys on>  as bucket
  , count(*)                            as rows
  , round(100.0 * count(*) / sum(count(*)) over (), 2) as pct
from {{ source('online_retail', 'online_retail_raw') }}
group by 1
order by rows desc
limit 50;
```

Then ask the question that matters: **what does my rule miss?**

```sql
-- Rows that look like the thing but do NOT match the predicate.
select *
from {{ source('online_retail', 'online_retail_raw') }}
where not (<your predicate>)
  and <a broader, independent signal of the same condition>
limit 100;
```

If that second query returns rows, your rule is a pattern, not a rule. Widen it or
document precisely what it excludes and why. Prefix conventions on identifier columns
are the classic offender in this dataset.

## Step 3 — Write the SQL

```sql
{{ config(materialized='view') }}   -- 'table' for marts

with source as (

    select * from {{ source('online_retail', 'online_retail_raw') }}

),

renamed as (

    select
          invoiceno    as invoice_no
        , stockcode    as stock_code
        -- ...
    from source

),

typed as (

    -- TRY_CAST, never CAST — failures become null and get surfaced by a test,
    -- rather than aborting the build or silently vanishing.
    select
          invoice_no
        , try_cast(quantity as number)      as quantity
        , try_cast(unitprice as float)      as unit_price
        , try_to_timestamp_ntz(invoicedate) as invoiced_at
    from renamed

),

flagged as (

    -- One named flag per business rule. The name says what it means; the
    -- schema.yml description says what the rule is and why.
    select
          typed.*
        , <predicate> as is_<rule>
    from typed

)

select * from flagged
```

House style: lowercase keywords, leading commas, one CTE per transformation step, CTEs
named for their contents (`source`, `renamed`, `typed`, `flagged`, `final`).

## Step 4 — Write the `schema.yml` entry in the same change

```yaml
version: 2

models:
  - name: stg_online_retail
    description: >
      One row per source line item, typed and flagged. Grain: <declare it>.
      Dedup: <what was removed, how many rows, and what "duplicate" means here>.
      Rules: <name each flag and state the rule in one sentence>.
    columns:
      - name: <grain key>
        description: <what it identifies>
        tests:
          - unique
          - not_null

      - name: is_cancelled
        description: <the rule, stated explicitly — not "whether it is cancelled">
        tests:
          - not_null
          - accepted_values:
              values: [true, false]
```

Two rules about tests, both learned the hard way on this dataset:

- **`not_null` asserts reality, not hope.** Roughly 25% of `CustomerID` is legitimately
  missing (guest checkouts). Query the null rate before adding `not_null` to any
  column. A test that fails on correct data is worse than no test.
- **Every filtering mart carries a test proving the filter held.** If `fct_revenue`
  excludes cancellations, add a singular test in `dbt/tests/` that fails if a
  non-revenue row is present in the output:

  ```sql
  -- dbt/tests/assert_fct_revenue_excludes_non_revenue.sql
  -- Returns rows only on failure.
  select *
  from {{ ref('fct_revenue') }}
  where extended_revenue <= 0
     or <any other condition the mart claims to have excluded>
  ```

## Step 5 — Build it and report honestly

```bash
dbt build --select <model_name>          # runs the model and its tests
dbt build --select +<model_name>         # include upstream, if you changed it too
```

Then report, in this shape:

- the command you ran and whether it passed;
- **row count before, after, delta, and the reason** for the delta;
- any rule you encoded, and — explicitly — what it does *not* catch.

If you did not run it, say you did not run it. Do not describe an untested model as
done.

## Definition of done

- [ ] Layer stated and correct — no filtering in Silver, no rule re-derivation in Gold
- [ ] Rule derived from a query against the data, and the "what does it miss" query run
- [ ] `.sql` follows house style, uses `ref()`/`source()`, hardcodes no database or schema
- [ ] `schema.yml` entry exists: grain declared, every column described, tests attached
- [ ] `not_null` tests verified against the actual null rate, not assumed
- [ ] Any filtering mart has a singular test proving the exclusion held
- [ ] `dbt build --select <model>` run and passing
- [ ] Row-count delta reported and explained
