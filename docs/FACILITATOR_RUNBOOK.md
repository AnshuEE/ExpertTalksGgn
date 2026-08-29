# Facilitator Runbook — Production-Ready AI for Data Engineering

Expert Talks Gurgaon · 60 minutes · Anshu Aggarwal & Ankur Jain

**The thesis you are proving on stage:** the harness comes first. Beats 2 and 3 are
three supervised steps with a human in the loop. Beat 4 is one prompt doing the same
work unattended. The difference between them is not a better model — it is
`CLAUDE.md`, `AGENTS.md`, and a skill file, committed before any data was touched.
Say that out loud in the recap. It is the whole session.

---

## 0. Fill this in before rehearsal

Four values are deliberately not hardcoded anywhere in the repo — `CLAUDE.md`'s own
convention is that connection details live in environment variables only. Fill them in
here, export them, and never type them into a tracked file.

| Value | Yours | Notes |
|---|---|---|
| `SNOWFLAKE_ACCOUNT` | `________` | org-account identifier |
| `SNOWFLAKE_USER` | `________` | SSO principal |
| `SNOWFLAKE_ROLE` | `________` | needs `CREATE GIT REPOSITORY`, `CREATE STREAMLIT`, Cortex usage |
| `SNOWFLAKE_WAREHOUSE` | `________` | XS is fine; **set auto-suspend ≥ 5 min** so you don't cold-start on stage |
| Cortex model | `________` | determined by the probe in §1.3 — do not assume |
| Git remote URL | `________` | needed for the API integration prefix |
| `JIRA_BASE_URL` / `JIRA_TICKET` | `________` | e.g. `https://<org>.atlassian.net`, `ETG-1234` |

```bash
export SNOWFLAKE_ACCOUNT=... SNOWFLAKE_USER=... SNOWFLAKE_ROLE=... \
       SNOWFLAKE_WAREHOUSE=... SNOWFLAKE_DATABASE=EXPERT_TALK
export JIRA_BASE_URL=... JIRA_EMAIL=... JIRA_API_TOKEN=... JIRA_TICKET=ETG-1234
```

---

## 1. Pre-session setup

Do this the **day before**, then re-verify 20 minutes before you go on. Not five
minutes before — the Git integration in §1.4 needs an `ACCOUNTADMIN`-level grant, and
discovering that at T-5 is how demos die.

### 1.1 Snowflake objects

```sql
use role <SNOWFLAKE_ROLE>;

create database if not exists EXPERT_TALK;
create schema   if not exists EXPERT_TALK.BRONZE;
create schema   if not exists EXPERT_TALK.SILVER;
create schema   if not exists EXPERT_TALK.GOLD;

-- Auto-suspend long enough to survive the deck sections between beats.
alter warehouse <SNOWFLAKE_WAREHOUSE> set auto_suspend = 300;
```

### 1.2 SSO session — the single biggest live risk

Auth is `externalbrowser`. A browser window opens on connect, and the Beat 4 one-shot
runs unattended for several minutes.

- Set `CLIENT_SESSION_KEEP_ALIVE = True` in both `profiles.yml` and the loader's
  connection config. Verify it is actually set — this is not the default.
- **Authenticate during the deck sections, not at the start of a beat.** Run a
  throwaway `select 1` at roughly the 15-minute mark while you're still on slides. The
  session is then warm for all four beats.
- Close every other Snowsight tab. A stale session in another tab can steal the
  callback and put an unexpected browser window on the projector.
- Rehearse the failure: if auth drops mid-Beat-4, you stop the agent, re-auth, and
  restart from the tag (§1.5). You do not let it retry — each retry opens a window.

### 1.3 Probe which Cortex models this region actually serves

Do not assume. Availability is region-dependent and this fails silently in rehearsal
if you only ever test the happy path.

```sql
select snowflake.cortex.complete('claude-3-5-sonnet', 'Reply with the single word OK.');
```

If that errors, work down the list until one returns: `claude-3-5-sonnet` →
`mistral-large2` → `llama3.1-70b` → `snowflake-arctic`. Record the winner in §0 and use
it consistently in Beats 3 and 4 — a model swap between beats changes the findings and
undercuts the comparison.

Also time it. A cold Cortex call on a large prompt can take 20–40 seconds. Know the
number so you can fill the silence deliberately instead of watching a spinner.

### 1.4 Git repository object

`CREATE API INTEGRATION` requires `ACCOUNTADMIN` or an explicit `CREATE INTEGRATION`
grant. Sort the grant first.

```sql
use role accountadmin;   -- or a role with CREATE INTEGRATION

create or replace secret EXPERT_TALK.PUBLIC.git_pat
    type     = password
    username = '<git username>'
    password = '<personal access token, repo:read scope>';

create or replace api integration expert_talk_git_api
    api_provider = git_https_api
    api_allowed_prefixes = ('https://github.com/<org>')
    allowed_authentication_secrets = (EXPERT_TALK.PUBLIC.git_pat)
    enabled = true;

use role <SNOWFLAKE_ROLE>;

create or replace git repository EXPERT_TALK.PUBLIC.expert_talk_repo
    api_integration = expert_talk_git_api
    git_credentials = EXPERT_TALK.PUBLIC.git_pat
    origin          = '<git remote url>.git';

alter git repository EXPERT_TALK.PUBLIC.expert_talk_repo fetch;
ls @EXPERT_TALK.PUBLIC.expert_talk_repo/branches/main/;
```

That last `ls` must list your files. If it returns nothing, the fetch didn't land and
`CREATE STREAMLIT` in Beat 4 will fail with a confusing path error.

**Burn this into muscle memory: `ALTER GIT REPOSITORY ... FETCH` after every push.**
Snowflake serves the fetched snapshot, not the live remote. Ninety percent of "the
dashboard didn't update" is a missing FETCH, and it will happen to you live.

### 1.5 Tag checkpoints — your recovery mechanism

Tag at the end of each beat. If a beat goes sideways, you reset to the previous tag and
carry on rather than debugging in front of the room.

```bash
git tag beat1-harness      # end of Beat 1
git tag beat2-bronze       # end of Beat 2
git tag beat3-cortex       # end of Beat 3
```

Also prepare, on a branch you never show: a `demo-safety-net` branch with the fallback
files from Appendix C already committed and the Streamlit app already deployed. If
Beat 4 fails outright, you switch to it, show the working dashboard, and narrate what
the agent *would* have produced. An honest recovery is a better demo moment than a
silent failure.

### 1.6 Snowflake MCP server (optional)

If you want the agent querying Snowflake conversationally during Beats 2–3, configure
the MCP server before the session and verify it in the same shell you'll present from.

Worth saying out loud when you do: this is exactly slide 13's decision rule. The MCP
server earns its place in Beats 2–3 because the agent is *reasoning across* a
profiling workflow. The Jira write-back in Beat 4 is a single deterministic HTTP call,
so it's a `curl`, not an integration. Pointing at that split live makes slide 13
concrete instead of abstract.

### 1.7 Final pre-flight (T-20 minutes)

- [ ] `select 1` against Snowflake succeeds — SSO session warm
- [ ] Cortex probe returns; chosen model recorded
- [ ] `ls @...expert_talk_repo/branches/main/` lists files
- [ ] `data/raw/Online_Retail.xlsx` present, 541,909 data rows
- [ ] `git log --oneline` shows the harness commit and nothing after it
- [ ] Terminal font ≥ 18pt, editor at high contrast, notifications silenced
- [ ] `demo-safety-net` branch exists and its dashboard loads
- [ ] Warehouse resumed and warm

---

## 2. Run of show

Beat 1 runs live **inside deck section 03**, right after slide 15 (`agent.md` vs
`claude.md`) — the slide describes those two files, so show the actual files rather
than the bullet points. Beats 2–4 run in section 05.

| Clock | Duration | Content | Deck |
|---|---|---|---|
| 00:00 | 3 min | Title, speakers, agenda | 1–3 |
| 00:03 | 8 min | Evolution of GenAI, core thesis, pulse check, 6 stages, mindset shift | 4–8 |
| 00:11 | 6 min | Token economy, investment levels, ~100 keywords, guardrails as cost control | 9–13 |
| 00:17 | 3 min | Context engineering opener; set up the two files | 14–15 |
| **00:20** | **4 min** | **BEAT 1 — the harness, live** | — |
| 00:24 | 4 min | Trust, maturity ladder, plan & execute with AI | 16–19 |
| 00:28 | 3 min | Advanced context tools: graphify, model-agnostic skills | 20–22 |
| 00:31 | 2 min | Case study framing | 23–24 |
| **00:33** | **5 min** | **BEAT 2 — guided Bronze build** | — |
| **00:38** | **5 min** | **BEAT 3 — Cortex finds the gaps** | — |
| **00:43** | **8 min** | **BEAT 4 — the one-shot finale** | — |
| 00:51 | 4 min | Recap: name the human-judgment moments, land the thesis | 26 |
| 00:55 | 5 min | Q&A | 26 |

**Where the slack is.** Slides 16–22 (00:24–00:31) are the compressible block — you can
take three minutes out of them without losing the argument. Do not borrow time from the
recap; the recap is where the thesis lands, and a demo that runs long and skips it has
shown four tricks and made no point.

**Beat 4's 8 minutes** are roughly 1 min setup, 3–4 min of agent runtime you talk over,
and 3 min of review. Plan what you say during the runtime — see §6.

---

## 3. BEAT 1 — Show the harness, not just the code (4 min)

**Screen:** editor, repo open, `git log` visible. Nothing but the harness files exist.

### Framing (say this)

> "Before we write a single line that touches data, look at what's already in this repo.
> There's no pipeline here. No models, no loader, no dashboard. What there is, is
> constraints.
>
> This is the part that usually gets skipped. People open a chat window and start
> prompting. We're going to spend four minutes on the files that make the next twenty
> minutes work — and then, at the end, I'm going to show you exactly what those four
> minutes bought us."

Plant that last sentence deliberately. It's the setup for the Beat 4 payoff.

### Walk `AGENTS.md` — the meaning (90 sec)

Open it at the **domain vocabulary table** and put it on screen. This is your slide-12
callback and the strongest thirty seconds in Beat 1.

> "Slide twelve — the word 'model'. Here it is as an actual artifact. In this repo,
> 'model' means a dbt model. Not an ML model, not a Databricks model, not the LLM.
> The LLM is called 'the LLM.' That row costs me nothing to write and saves a
> correction on every single prompt for the rest of the session.
>
> About a hundred words like this cover almost everything we say to a model in a day.
> That's the token economy argument made concrete: I'm not buying a bigger context
> window, I'm removing the ambiguity that made me need one."

Then scroll to the dataflow diagram:

> "Model-agnostic, deliberately. This exact file works with Claude, GPT, or Gemini. It
> describes what the project *means*."

### Walk `CLAUDE.md` — the rules (90 sec)

> "And this one is the rulebook — how work gets done. Three rules I want you to hold on
> to, because you'll watch all three get tested in the next fifteen minutes."

Land these three, in this order:

1. **"Bronze never cleans."** — "Every column a string. `Quantity` is a string.
   `CustomerID` arrives from Excel as `17850.0` and stays as the text `17850.0`. That
   looks wrong. It is the most important rule in the file, because it means every later
   decision is auditable against something nobody touched."
2. **"Tests ship with the thing they test."** — "Not 'add tests after.' A model without
   tests is a draft. Slide five said the guardrails you need already existed before AI —
   this is where that stops being a platitude."
3. **"Don't call it done without running it."** — "It has to name the command it ran. If
   it couldn't run it, it says so. This one line is worth more than any prompt-
   engineering trick I know."

### Walk the skill (60 sec)

Open `.claude/skills/create-dbt-model/SKILL.md`, scroll to Step 2 and the "definition of
done" checklist.

> "A skill is a workflow written down once. Look at step two — before you encode any
> rule that excludes rows, run a query that shows what your rule *misses*. Not think
> about it. Run it.
>
> And notice this is markdown and SQL, not a Claude-specific format. Slide twenty-two:
> skills should work for any model, not one tool. The second time we use this it's
> nearly free, and the tenth time it's still enforcing the same standard."

Commit and tag:

```bash
git add CLAUDE.md AGENTS.md .claude/skills docs/ .gitignore
git commit -m "chore(harness): ETG-1234 add context files, dbt model skill, review checklist"
git tag beat1-harness
```

> "That's committed. It now survives every branch we make for the rest of the session.
> Hold that thought."

**Do not** open `docs/ai_review_checklist.md` on screen — it names quirks the audience
should watch Cortex discover in Beat 3.

---

## 4. BEAT 2 — Guided Bronze build (5 min)

**Screen:** terminal with the agent, Snowsight in a second tab.

### The prompt (type it live, don't paste)

```
Load data/raw/Online_Retail.xlsx into EXPERT_TALK.BRONZE.ONLINE_RETAIL_RAW,
following the Bronze rules in CLAUDE.md.

Write it as a re-runnable script in src/bronze/, not a console upload. Show me
your plan before you write anything.
```

Typing it matters. It's short, it names the file, it names the target, and it delegates
the rules to `CLAUDE.md` rather than restating them — which is the point. Say so:

> "Notice what's not in that prompt. I didn't say 'make every column a string.' I didn't
> say 'don't filter cancellations.' That's in the harness. The prompt is the task; the
> harness is the standard."

### What a good draft gets right

- Every column typed `STRING`, including `Quantity` and `UnitPrice`
- The three metadata columns (`_LOADED_AT`, `_SOURCE_FILE`, `_SOURCE_ROW`) and nothing else
- A `CREATE OR REPLACE` / truncate-and-load shape, so re-running is idempotent
- A row-count assertion against the source sheet
- `pytest` coverage in `tests/`, AAA comments present
- Connection values pulled from env vars

### What it commonly misses — watch for these

These are the human-judgment moments. Name them out loud as you catch them; the recap
depends on the audience having seen them.

| Miss | Why it matters | What to say |
|---|---|---|
| `CustomerID` written as `17850` not `17850.0` | pandas read it as float and the agent "helpfully" cleaned it | "That's a cast. In Bronze. It looks like a fix and it's a layer violation — I've now lost the evidence of what Excel actually did." |
| Header row or trailing blank rows counted into the total | Bronze row count must be exactly the source count | "Before, after, delta. Check four on our review list. What's the number and why?" |
| `NaN` written as the literal string `"nan"` | pandas artifact leaking into the warehouse as data | "Is that in the source file, or did our loader invent it?" |
| Row-count assertion written but never run | "Done" without evidence | "You said it's done. Which command did you run?" |
| Tests deferred | `CLAUDE.md` says same change | "Tests ship with the thing they test. Same commit." |

Verify in Snowsight, on screen:

```sql
select count(*) from EXPERT_TALK.BRONZE.ONLINE_RETAIL_RAW;   -- expect 541,909
select * from EXPERT_TALK.BRONZE.ONLINE_RETAIL_RAW limit 20;
```

Point at a `17850.0` in the output:

> "There it is. Ugly, and correct. Bronze is supposed to look like the source, not like
> what we wish the source was."

```bash
git tag beat2-bronze
```

---

## 5. BEAT 3 — Cortex finds the gaps (5 min)

**Screen:** Snowsight worksheet. This beat is SQL, not the agent.

### Framing

> "Normally this is where I'd spend an afternoon. Eyeball a few thousand rows, run
> twenty `group by`s, build a mental list of everything wrong with this data. Instead
> we're going to hand a sample and some column statistics to a model that's running
> inside Snowflake — no semantic model, no Cortex Analyst setup, just a function call in
> a worksheet — and ask it what's wrong.
>
> I've worked this dataset. I know what's in there. Watch what it finds, and watch what
> it doesn't — because both are the honest answer."

### The query

```sql
with col_stats as (
    select 'InvoiceNo'   as col, count(*) as n, count(invoiceno)   as non_null, count(distinct invoiceno)   as distinct_vals, min(invoiceno)   as lo, max(invoiceno)   as hi from EXPERT_TALK.BRONZE.ONLINE_RETAIL_RAW
    union all select 'StockCode',   count(*), count(stockcode),   count(distinct stockcode),   min(stockcode),   max(stockcode)   from EXPERT_TALK.BRONZE.ONLINE_RETAIL_RAW
    union all select 'Description', count(*), count(description), count(distinct description), min(description), max(description) from EXPERT_TALK.BRONZE.ONLINE_RETAIL_RAW
    union all select 'Quantity',    count(*), count(quantity),    count(distinct quantity),    to_varchar(min(try_cast(quantity as number))),   to_varchar(max(try_cast(quantity as number)))   from EXPERT_TALK.BRONZE.ONLINE_RETAIL_RAW
    union all select 'InvoiceDate', count(*), count(invoicedate), count(distinct invoicedate), min(invoicedate), max(invoicedate) from EXPERT_TALK.BRONZE.ONLINE_RETAIL_RAW
    union all select 'UnitPrice',   count(*), count(unitprice),   count(distinct unitprice),   to_varchar(min(try_cast(unitprice as float))),  to_varchar(max(try_cast(unitprice as float)))  from EXPERT_TALK.BRONZE.ONLINE_RETAIL_RAW
    union all select 'CustomerID',  count(*), count(customerid),  count(distinct customerid),  min(customerid),  max(customerid)  from EXPERT_TALK.BRONZE.ONLINE_RETAIL_RAW
    union all select 'Country',     count(*), count(country),     count(distinct country),     min(country),     max(country)     from EXPERT_TALK.BRONZE.ONLINE_RETAIL_RAW
),

profile as (
    select listagg(
        col || ' | rows=' || n
            || ' | nulls=' || (n - non_null) || ' (' || round(100.0 * (n - non_null) / nullif(n,0), 1) || '%)'
            || ' | distinct=' || distinct_vals
            || ' | min=' || coalesce(left(lo, 40), 'NULL')
            || ' | max=' || coalesce(left(hi, 40), 'NULL')
        , '\n') within group (order by col) as txt
    from col_stats
),

sample as (
    select listagg(
        coalesce(invoiceno,'~') || ' | ' || coalesce(stockcode,'~') || ' | ' || coalesce(left(description,35),'~')
        || ' | ' || coalesce(quantity,'~') || ' | ' || coalesce(invoicedate,'~')
        || ' | ' || coalesce(unitprice,'~') || ' | ' || coalesce(customerid,'~') || ' | ' || coalesce(country,'~')
        , '\n') as txt
    from (select * from EXPERT_TALK.BRONZE.ONLINE_RETAIL_RAW sample (120 rows))
)

select snowflake.cortex.complete(
    '<CORTEX_MODEL>',
    'You are a senior data engineer reviewing a raw retail transactions table before it '
    || 'is transformed into a revenue mart. Every column was loaded as STRING with no cleaning.\n\n'
    || 'COLUMN STATISTICS:\n' || profile.txt
    || '\n\nRANDOM SAMPLE (InvoiceNo | StockCode | Description | Quantity | InvoiceDate | UnitPrice | CustomerID | Country):\n'
    || sample.txt
    || '\n\nList the data-quality issues that would corrupt a revenue calculation if this table '
    || 'were aggregated naively. For each issue give: (1) the issue, (2) the evidence in the stats '
    || 'or sample that shows it, (3) roughly how many rows you think are affected, (4) which layer '
    || 'should fix it and how. Be specific about column values. Call out anything where a naive '
    || 'filter would look correct but silently miss rows. Rank by revenue impact.'
) as findings
from profile, sample;
```

Substitute `<CORTEX_MODEL>` with the model from §1.3. Expect 20–40 seconds — narrate
the prompt construction while it runs: *"the whole trick is that it never sees the
table, only a sample and eight rows of statistics — that's a few thousand tokens
standing in for half a million rows."*

### What it should surface (facilitator's reference — do not pre-announce)

| Issue | Actual scale | Likelihood it's found |
|---|---|---|
| Missing `CustomerID` | ~135,080 rows (~25%) | Near-certain — it's the loudest stat |
| Cancelled orders, `InvoiceNo` starts `C` | 9,288 rows | Near-certain — visible in the sample |
| Negative / zero `Quantity` | 10,624 rows | Near-certain — min is negative in the stats |
| Negative / zero `UnitPrice` | 2,517 rows | Likely |
| `CustomerID` stored as float (`17850.0`) | all non-null | Likely — obvious in the sample |
| Non-merchandise `StockCode`s (`POST`, `D`, `M`, `DOT`, `AMAZONFEE`, gift cards) | 37 codes | Coin-flip — depends on the sample draw |
| Exact duplicate rows | 5,268 rows | Unlikely — a random sample can't show it |
| Case-inconsistent `StockCode` (`15056BL` / `15056bl`) | — | Unlikely |
| **`A`-prefix "Adjust bad debt" rows (two at −£11,062.06)** | **a handful of rows** | **Very unlikely — single-digit rows in 541,909** |

**Read the output live and mark it honestly.** Tick what it caught. Then:

> "It found the big ones, and it found them in about thirty seconds. Here's what it
> missed, and this is the more useful half of the demo."

On duplicates:

> "It couldn't have found this. A random sample can't show you duplicates — that's a
> `group by` over the whole table, not a sampling question. This isn't the model being
> weak, it's me giving it the wrong instrument. That's my job, not its job."

On the `A`-prefix rows — **do this one live, it's the sharpest moment in the session:**

```sql
select left(invoiceno,1) as prefix, count(*) as rows,
       round(sum(try_cast(quantity as number) * try_cast(unitprice as float)), 2) as amount
from EXPERT_TALK.BRONZE.ONLINE_RETAIL_RAW
group by 1 order by rows desc;
```

> "Look at the prefixes. `C` for cancellations, nine thousand rows — everyone knows that
> one, it's in every tutorial about this dataset. And then `A`. A handful of rows.
> 'Adjust bad debt', eleven thousand pounds a time."

**Read the actual row count and amount off the screen** — don't quote a number from this
runbook. The `amount` column in that query gives you the real figure live, and quoting it
from the result is both accurate and more convincing than a rehearsed statistic.

> "That's a rounding error in row terms and very much not a rounding error in pounds.
> Cortex didn't find it, and honestly, neither would most engineers reading a sample. But
> if you write `where invoice_no not like 'C%'` — which is what everyone writes — those
> rows land in your revenue mart and move the number.
>
> This is check one on our review list: is it a rule, or a pattern that happened to fit?
> The AI gave me the list in thirty seconds. Deciding that this specific gap matters —
> that's still mine."

*If Cortex does find the `A` rows:* say so with genuine credit — "it got one I didn't
expect, and it got it from two rows in a sample" — then pivot to duplicates, which it
structurally cannot find. The point survives either way, and honesty about which
happened is more persuasive than a scripted win.

```bash
git tag beat3-cortex
```

---

## 6. BEAT 4 — The one-shot finale (8 min)

### Setup (60 sec) — the setup *is* the argument

```bash
git status                      # show Beats 2–3 work uncommitted
git stash                       # or: leave it, and branch away from it
git checkout -b ETG-1234-one-shot-pipeline
ls                              # CLAUDE.md, AGENTS.md, .claude/, docs/ — still here
```

> "New branch. The loader we wrote together — gone. The Cortex query — gone. Everything
> from the last ten minutes, left behind.
>
> What came with us is the harness. `CLAUDE.md`, `AGENTS.md`, the skill. Committed in
> Beat 1, before we touched any data.
>
> One prompt. Ingest, profile, three layers, dashboard, Jira. No steering."

### The one-shot prompt

Paste this one — it's long by design, and the length is the point. Have it in a file
you can `cat` if paste fails.

```
Read CLAUDE.md and AGENTS.md before you start. They define the layer rules, naming
conventions, testing standard, and domain vocabulary for everything below — follow
them over any default you would otherwise reach for. Use the create-dbt-model skill
for every dbt model you write.

Build the pipeline end to end on this branch:

1. BRONZE. Write a re-runnable loader in src/bronze/ and load
   data/raw/Online_Retail.xlsx into EXPERT_TALK.BRONZE.ONLINE_RETAIL_RAW. Every
   source column STRING, plus only the load-metadata columns CLAUDE.md permits. No
   cleaning, casting, filtering, or dedup. Assert the loaded row count equals the
   source sheet row count and print both. Add pytest coverage in tests/.

2. PROFILE. Write sql/cortex/profile_bronze.sql: a single ad-hoc
   SNOWFLAKE.CORTEX.COMPLETE() call fed a random sample of Bronze rows plus
   per-column statistics (row count, null count and rate, distinct count, min, max),
   asking it to enumerate the data-quality issues that would corrupt a revenue
   calculation. Use the model '<CORTEX_MODEL>'. Run it, and paste its findings
   verbatim into your response before you act on them.

3. SILVER. Build stg_online_retail. Type defensively with TRY_CAST, dedup exact
   duplicate rows, and add a named boolean flag for each business rule you identify.
   Silver keeps every row — flag, never filter.

   For every rule you write, before you write it: run a query showing the full
   distribution of the values the rule keys on, and a second query showing rows that
   meet the rule's INTENT but not its PREDICATE. Paste both queries and their results.
   Do not assume a naming or prefix convention holds across the dataset without
   measuring its coverage. If the second query returns rows, widen the rule.

   Verify actual null rates before adding any not_null test. Do not add one to a
   column that is legitimately null in normal operation.

4. GOLD. Build fct_revenue as a table. Exclude non-revenue rows by referencing
   Silver's flags — never by re-deriving a rule inline. Declare the grain and enforce
   it with a uniqueness test. Add a singular test in dbt/tests/ that fails if any row
   the mart claims to exclude is present in its output. Add dim_customer only if
   fct_revenue needs it.

5. BUILD AND TEST. Run `dbt build` and `pytest tests/ -v`. Report the exact commands
   and their results. Report row counts at every layer: source file, Bronze, Silver
   after dedup, Gold after exclusions — with before, after, delta, and the reason for
   each delta. The named exclusions must account for the entire Bronze-to-Gold gap; if
   there is an unexplained residual, investigate it before continuing.

6. DASHBOARD. Write streamlit/app.py reading ONLY from EXPERT_TALK.GOLD — revenue
   over time, top products, revenue by country, and a headline total. Commit and push
   the branch, then deploy via the Git repository object: ALTER GIT REPOSITORY
   EXPERT_TALK.PUBLIC.expert_talk_repo FETCH, then CREATE OR REPLACE STREAMLIT from
   the branch path per CLAUDE.md. Return the app URL.

7. JIRA. Post an implementation comment to $JIRA_TICKET using curl against the Jira
   REST API with $JIRA_BASE_URL, $JIRA_EMAIL and $JIRA_API_TOKEN. Cover: what was
   built per layer, the business rules encoded and what each one deliberately excludes,
   row counts at every layer, and the tests added. Write it for a reviewer who was not
   in the room.

Work through all seven steps without stopping to confirm. Stop and ask only if
completing a step would require breaking a layer rule in CLAUDE.md.

Finish with: row counts per layer, every rule you encoded and explicitly what each one
does NOT catch, the commands you ran, the app URL, and the Jira comment link.
```

**Why it's built this way** — worth explaining to the audience while it runs:

- It **delegates the standard to the harness** and states only the task. No layer rules
  are restated; that's what Beat 1 bought.
- Step 3's *"rows that meet the intent but not the predicate"* instruction is the
  `A`-prefix trap defused **without naming it**. It's the skill's step 2, promoted into
  the prompt. It generalizes to gaps you haven't found yet.
- Step 5's *"exclusions must account for the entire gap"* makes an unexplained residual
  a blocking condition rather than a rounding error.
- *"Without stopping to confirm"* is what makes it a one-shot. The escape hatch is
  narrow and specific: a layer-rule violation, nothing else.
- The final report is specified up front, so the review in the last three minutes has
  something concrete to read.

### What to say during the 3–4 minutes it runs

Don't narrate the tool calls — the audience can read. Use the time:

> "Watch it read `CLAUDE.md` first. Nobody told it to at that moment — it's the first
> line of the prompt, and that's the entire difference between this and a chat window.
>
> Ten minutes ago I corrected it three times: the float cast, the row count, the missing
> tests. Same model. Same dataset. The only thing that changed is that the correction
> is now written down where it reads it, instead of in my head where it doesn't.
>
> This is slide seventeen's maturity ladder — we just walked from stage three to stage
> four live, and the thing that moved us wasn't capability. It was context."

### Review it (3 min) — checks 1, 4, 5

1. **Row counts.** Source = Bronze. Does the Bronze→Gold gap fully decompose into named
   exclusions?
2. **The cancellation rule.** Open the Silver YAML. Did the coverage query run? Does the
   rule catch `A` as well as `C`? Land it either way:
   - *Caught it:* "It ran the distribution query, found the `A` prefix, and widened the
     rule. That's the skill file doing its job — not the model getting luckier."
   - *Missed it:* "It didn't catch it. Ten minutes ago that was a surprise; now it's a
     one-line fix in the skill file and it never happens again. That's the compounding
     on slide twenty-six — and I'd rather show you a harness that improves than a demo
     that pretends."
3. **Open the dashboard.** Numbers on screen, sourced from Gold.
4. **Open the Jira comment.** Slide 24's third card, closed.

---

## 7. Recap (4 min) — do not skip this

Slide 26 up. Then make the contrast explicit — the audience saw both halves, but they
won't draw the line themselves.

> "Three moments in Beats two and three needed a human, and I want to name them
> precisely.
>
> **One.** The loader stripped `.0` off `CustomerID`. Sensible-looking cleanup, wrong
> layer, and it destroyed the evidence of what Excel did. I caught that because a file
> in this repo says Bronze never cleans.
>
> **Two.** Cortex couldn't find the duplicate rows. Not a weakness of the model — I
> handed it a random sample, and duplicates are a `group by` over the whole table.
> Wrong instrument, and choosing the instrument was my job.
>
> **Three.** A handful of rows out of five hundred and forty-one thousand, prefixed `A`
> instead of `C` — bad-debt adjustments worth eleven thousand pounds each. Cortex missed
> them. Most engineers miss them. Knowing that a prefix convention is a pattern and not a
> rule — that's judgment, and it stayed mine.
>
> Then Beat four did all of it in one prompt. Same model. Same data. What changed is
> that all three of those corrections had been written down — in `CLAUDE.md`, in
> `AGENTS.md`, in a skill file — before we touched a single row.
>
> That's the whole session. The bottleneck was never model capability. It was trust,
> and trust is engineered. The four minutes we spent in Beat one is what made Beat four
> possible, and the second and tenth and hundredth time you use that harness, it's
> nearly free.
>
> AI bridges engineering gaps. Exceptional data engineering is what fills them in the
> first place."

Share the repo link. Move to Q&A.

### Likely questions, short answers

| Question | Answer |
|---|---|
| "How long did the harness take to write?" | An afternoon, once. It's been reused across every project since — that's the compounding, not the writing. |
| "Would this work with GPT or Gemini?" | `AGENTS.md` and the skill are deliberately model-agnostic — markdown and SQL, no vendor format. `CLAUDE.md` is the Claude-specific rulebook; the equivalent for another tool is a different file, same content. |
| "What if the agent ignores CLAUDE.md?" | It sometimes does — that's why the review checklist and the dbt tests exist. Context makes the right thing likely; tests make the wrong thing visible. You need both. |
| "Isn't this a lot of ceremony for a demo?" | It's less ceremony than one wrong revenue number in a board deck. And this dataset had that number in it — two rows. |
| "Why Cortex rather than an external API?" | The data never leaves Snowflake, and it's a SQL function — no new service, no egress review. |
| "Do you let it run unattended in production?" | Not against production data. The one-shot is scoped to a branch, and there's a PR and a human before anything merges. Slide 19: explicit permissions on irreversible operations. |

---

## Appendix A — Prompt library

**Beat 2 — Bronze ingestion**
```
Load data/raw/Online_Retail.xlsx into EXPERT_TALK.BRONZE.ONLINE_RETAIL_RAW,
following the Bronze rules in CLAUDE.md.

Write it as a re-runnable script in src/bronze/, not a console upload. Show me
your plan before you write anything.
```

**Beat 2 — challenge prompts** (pick whichever the draft earns)
```
You cast CustomerID to an integer. Which CLAUDE.md rule does that break, and what
evidence did it destroy?
```
```
You said it's done. Which command did you run, and what did it print?
```
```
Row count before, after, delta, and the reason. All four.
```

**Beat 3 — narrowing after the Cortex findings**
```
Cortex listed N issues. Which of them can it NOT have detected from a random sample
plus column statistics, and why? Write the query that would actually find those.
```

**Beat 4 — one-shot**: see §6.

**Beat 4 — recovery, if the one-shot stalls mid-run**
```
Continue from where you stopped. Do not restart completed steps. State which step
you are resuming and what you had already finished.
```

**Beat 4 — recovery, if a rule came out naive**
```
Your cancellation rule keys on a single InvoiceNo prefix. Run the full prefix
distribution over Bronze with row counts and summed amounts, then tell me what your
rule misses and what it costs.
```

---

## Appendix B — Live-demo risk register

| Risk | Likelihood | Mitigation | If it happens live |
|---|---|---|---|
| SSO session expires mid-Beat-4 | **High** | `CLIENT_SESSION_KEEP_ALIVE`, authenticate at ~15 min | Stop the agent immediately. Re-auth, resume with the recovery prompt. Never let it retry — each retry opens a browser window. |
| Cortex latency 40s+ or timeout | Medium | Time it in rehearsal; §1.3 fallback models | Talk over it — the prompt-construction explanation fills 40 seconds. If it times out, drop `sample (120 rows)` to 60. |
| Chosen Cortex model unavailable | Low (if probed) | §1.3 probe, day before | Swap to the next fallback and say why out loud — it's an honest platform constraint. |
| `CREATE STREAMLIT` fails on path | Medium | `ls @repo/branches/<b>/` in pre-flight | Almost always a missing `ALTER GIT REPOSITORY ... FETCH`, or the branch wasn't pushed. Check both, in that order. |
| Git integration missing grants | Low | §1.4, day before | Not fixable live. Fall back to `demo-safety-net`. |
| Warehouse cold-start pause | Medium | `auto_suspend = 300`, warm in pre-flight | Narrate it: "that's a cold warehouse — worth knowing your suspend settings before a demo." |
| One-shot partially completes (e.g. Gold built, Streamlit not) | **Medium** | Prompt orders dashboard late so failure lands after the data work | Show what completed, use the recovery prompt for the rest. A partial one-shot that reports honestly is still a strong demo — it's literally the trust argument. |
| One-shot produces a naive `C`-only rule | Medium | Step 3's coverage-query instruction | **Do not hide it.** Run the prefix distribution live, show the gap in pounds, fix the skill file. This is the strongest available recovery — it turns a miss into the thesis. |
| Agent expands scope / wanders | Low | `CLAUDE.md` "never expand scope"; prompt's narrow escape hatch | Interrupt, restate the step, continue. |
| Network drops entirely | Low | — | `demo-safety-net` branch + screenshots of the deployed dashboard. Keep a local screenshot set on disk. |
| Jira 401 | Medium | Test the `curl` in pre-flight | Skip it, show the drafted comment text. It's the least load-bearing step in the beat. |
| Overrun into the recap | **High** | Slides 16–22 are the compressible block | Cut Beat 4's review to row counts + dashboard only. Never cut the recap. |

---

## Appendix C — Known-good fallback artifacts

Deliberately kept **in this document only**, not as files in `sql/`, `dbt/`, or `src/`.
The repo must be empty of pipeline code when Beat 1 opens, or Beat 1's framing is a lie.
Keep them committed on `demo-safety-net`.

### C.1 `profiles.yml.example`

```yaml
expert_talk:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      authenticator: externalbrowser
      role: "{{ env_var('SNOWFLAKE_ROLE') }}"
      warehouse: "{{ env_var('SNOWFLAKE_WAREHOUSE') }}"
      database: "{{ env_var('SNOWFLAKE_DATABASE') }}"
      schema: SILVER
      threads: 4
      client_session_keep_alive: true
```

### C.2 `dbt/macros/generate_schema_name.sql`

Without this, dbt concatenates and you get `SILVER_marts` instead of `GOLD`.

```sql
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
```

### C.3 `dbt_project.yml` (excerpt)

```yaml
name: expert_talk
profile: expert_talk
models:
  expert_talk:
    staging:
      +materialized: view
      +schema: SILVER
    marts:
      +materialized: table
      +schema: GOLD
```

### C.4 `dbt/models/staging/stg_online_retail.sql`

```sql
{{ config(materialized='view') }}

with source as (

    select * from {{ source('online_retail', 'online_retail_raw') }}

),

renamed as (

    select
          trim(invoiceno)        as invoice_no
        , upper(trim(stockcode)) as stock_code      -- 15056BL and 15056bl are one product
        , trim(description)      as description
        , quantity               as quantity_raw
        , invoicedate            as invoiced_at_raw
        , unitprice              as unit_price_raw
        , customerid             as customer_id_raw
        , trim(country)          as country
        , _source_row
    from source

),

typed as (

    select
          invoice_no
        , stock_code
        , description
        , try_cast(quantity_raw as number(38,0))                        as quantity
        , try_to_timestamp_ntz(invoiced_at_raw)                         as invoiced_at
        , try_cast(unit_price_raw as float)                             as unit_price
        -- via float: Excel wrote these as 17850.0, so a direct integer cast nulls them
        , try_cast(try_cast(customer_id_raw as float) as number(38,0))  as customer_id
        , country
        , _source_row
    from renamed

),

deduped as (

    select *
    from typed
    qualify row_number() over (
        partition by invoice_no, stock_code, description, quantity,
                     invoiced_at, unit_price, customer_id, country
        order by _source_row
    ) = 1

),

flagged as (

    select
          deduped.*
        , quantity * unit_price as extended_amount
        -- Prefix coverage was measured, not assumed: C = cancellations (9,288 rows),
        -- A = "Adjust bad debt" (single-digit row count, GBP 11,062.06 a time).
        -- Both are non-revenue; a C-only predicate leaks the A rows into the mart.
        , not regexp_like(invoice_no, '^[0-9]+$')                       as is_cancelled
        , quantity < 0 and regexp_like(invoice_no, '^[0-9]+$')          as is_return
        , coalesce(unit_price, 0) <= 0                                  as is_zero_or_negative_price
        , customer_id is not null                                       as has_customer
        -- Merchandise codes are 5 digits with an optional letter suffix. Everything
        -- else (POST, D, M, DOT, BANK CHARGES, AMAZONFEE, gift cards) is not a product.
        , not regexp_like(stock_code, '^[0-9]{5}[A-Z]*$')               as is_non_merchandise
    from deduped

)

select * from flagged
```

Note the `is_cancelled` predicate is written as "invoice number is not purely numeric"
rather than an enumeration of prefixes — it catches `C`, `A`, and any prefix the
dataset has that nobody has found yet. That is check 3 (does it generalize) applied to
check 1 (rule vs pattern).

### C.5 `dbt/models/staging/schema.yml`

```yaml
version: 2

sources:
  - name: online_retail
    database: EXPERT_TALK
    schema: BRONZE
    tables:
      - name: online_retail_raw

models:
  - name: stg_online_retail
    description: >
      One row per non-duplicate source line item, typed and flagged. Grain: _source_row.
      Dedup removes 5,268 byte-identical repeat rows (re-scans/re-exports), keeping the
      lowest _source_row. Flags: is_cancelled (invoice number not purely numeric —
      covers C-prefix cancellations and A-prefix bad-debt adjustments); is_return
      (negative quantity on a normal invoice); is_zero_or_negative_price;
      is_non_merchandise (stock code is not 5 digits + optional letters);
      has_customer (~25% of rows are guest checkouts and legitimately have none).
      Silver flags but never filters.
    columns:
      - name: _source_row
        description: 1-based row ordinal in the source sheet; the grain of this model.
        tests: [unique, not_null]
      - name: invoice_no
        tests: [not_null]
      - name: customer_id
        description: Null for ~25% of rows — guest checkouts. Deliberately no not_null test.
      - name: is_cancelled
        tests:
          - not_null
          - accepted_values: {values: [true, false]}
      - name: is_non_merchandise
        tests:
          - not_null
          - accepted_values: {values: [true, false]}
```

### C.6 `dbt/models/marts/fct_revenue.sql`

```sql
{{ config(materialized='table') }}

with silver as (

    select * from {{ ref('stg_online_retail') }}

),

revenue as (

    select
          _source_row as line_item_id
        , invoice_no
        , stock_code
        , description
        , customer_id
        , has_customer
        , country
        , invoiced_at
        , date_trunc('month', invoiced_at) as invoice_month
        , quantity
        , unit_price
        , extended_amount as revenue_amount
    from silver
    -- Exclusions reference Silver's flags; the rules themselves live in Silver.
    where not is_cancelled
      and not is_return
      and not is_zero_or_negative_price
      and not is_non_merchandise
      and quantity > 0
      and invoiced_at is not null

)

select * from revenue
```

### C.7 `dbt/models/marts/schema.yml`

```yaml
version: 2

models:
  - name: fct_revenue
    description: >
      One row per revenue-bearing line item. Grain: line_item_id (= Silver _source_row).
      Excludes, by Silver flag: cancellations and bad-debt adjustments, returns,
      zero/negative prices, non-merchandise line items (postage, fees, vouchers),
      non-positive quantities, and rows with an unparseable invoice date. Guest
      checkouts ARE included — they are real revenue; has_customer marks them.
    columns:
      - name: line_item_id
        tests: [unique, not_null]
      - name: revenue_amount
        tests: [not_null]
```

### C.8 `dbt/tests/assert_fct_revenue_excludes_non_revenue.sql`

```sql
-- Singular test: returns rows only on failure.
-- Proves every exclusion fct_revenue claims actually held.
select *
from {{ ref('fct_revenue') }}
where revenue_amount <= 0
   or quantity <= 0
   or unit_price <= 0
   or not regexp_like(invoice_no, '^[0-9]+$')       -- any C/A/other prefix leaked
   or not regexp_like(stock_code, '^[0-9]{5}[A-Z]*$')
   or invoiced_at is null
```

### C.9 `streamlit/app.py`

```python
import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Online Retail — Revenue", layout="wide")
session = get_active_session()

# Gold only. If a number isn't here, the fix is a Gold model, not a query in this file.
GOLD = "EXPERT_TALK.GOLD.FCT_REVENUE"

st.title("Online Retail — Revenue")

kpis = session.sql(f"""
    select sum(revenue_amount)    as total_revenue
         , count(*)               as line_items
         , count(distinct invoice_no) as invoices
         , count(distinct iff(has_customer, customer_id, null)) as customers
    from {GOLD}
""").to_pandas().iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Revenue", f"£{kpis.TOTAL_REVENUE:,.0f}")
c2.metric("Line items", f"{kpis.LINE_ITEMS:,}")
c3.metric("Invoices", f"{kpis.INVOICES:,}")
c4.metric("Known customers", f"{kpis.CUSTOMERS:,}")

st.subheader("Revenue by month")
st.bar_chart(
    session.sql(f"""
        select invoice_month, sum(revenue_amount) as revenue
        from {GOLD} group by 1 order by 1
    """).to_pandas().set_index("INVOICE_MONTH")
)

left, right = st.columns(2)

with left:
    st.subheader("Top 15 products")
    st.dataframe(session.sql(f"""
        select description, sum(quantity) as units, sum(revenue_amount) as revenue
        from {GOLD} group by 1 order by revenue desc limit 15
    """).to_pandas(), use_container_width=True)

with right:
    st.subheader("Top 15 countries")
    st.dataframe(session.sql(f"""
        select country, sum(revenue_amount) as revenue, count(distinct invoice_no) as invoices
        from {GOLD} group by 1 order by revenue desc limit 15
    """).to_pandas(), use_container_width=True)
```

### C.10 Streamlit deploy

```sql
alter git repository EXPERT_TALK.PUBLIC.expert_talk_repo fetch;

create or replace streamlit EXPERT_TALK.GOLD.expert_talk_dashboard
    root_location   = '@EXPERT_TALK.PUBLIC.expert_talk_repo/branches/ETG-1234-one-shot-pipeline/streamlit'
    main_file       = 'app.py'
    query_warehouse = <SNOWFLAKE_WAREHOUSE>;

show streamlits in schema EXPERT_TALK.GOLD;   -- the URL is in the output
```

### C.11 Jira comment (`curl`)

```bash
curl -sS -X POST \
  -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  "$JIRA_BASE_URL/rest/api/3/issue/$JIRA_TICKET/comment" \
  -d @- <<'JSON'
{
  "body": {
    "type": "doc", "version": 1,
    "content": [{"type": "paragraph", "content": [{"type": "text",
      "text": "Pipeline built end to end. Bronze: 541,909 rows, all STRING, no cleaning. Silver: 5,268 exact duplicates removed; flags is_cancelled / is_return / is_non_merchandise / has_customer, each documented in schema.yml. Gold: fct_revenue excludes cancellations (incl. A-prefix bad-debt adjustments), returns, non-positive prices and quantities, and non-merchandise line items. Tests: dbt schema + singular tests, pytest on the loader. Dashboard deployed to Streamlit-in-Snowflake reading Gold only."
    }]}]
  }
}
JSON
```
