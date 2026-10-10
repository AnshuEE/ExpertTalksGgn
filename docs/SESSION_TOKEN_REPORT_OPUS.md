# Session Token Report — Silver & Gold Build

**Session:** `922dd7f8-7695-4d18-a1c4-5b02795796f9`
**Date:** 2026-10-10
**Model:** `claude-opus-5` (1M context), single model for the whole session
**Measured with:** `src/scripts/token_usage.py` — see [TOKEN_TRACKING.md](TOKEN_TRACKING.md)

---

## 1. What the session was asked to do

> Create Silver and Gold dbt models for the online retail Bronze layer, and execute
> them in Snowflake.

**What was actually found:** the Silver and Gold models already existed in the repo,
complete with schema YAML and singular tests. Nothing needed to be written. What had
*not* happened was execution — `EXPERT_TALK.SILVER` and `EXPERT_TALK.GOLD` were empty
(`INFORMATION_SCHEMA.TABLES` returned zero rows for both schemas).

Per the project's "never expand scope without asking" rule, the models were **not**
rewritten. The session verified them, then built them.

---

## 2. Cost summary

| Metric | Value |
|---|---|
| Requests | 11 |
| Billable input tokens | 617,216 |
| Output tokens | 7,019 |
| **Estimated cost** | **$0.8792** |

Baseline at session start was 3 requests / $0.3163; the build work added 8 requests
and roughly $0.56.

### Per-model

| model | reqs | in (billable) | out | cost |
|---|---|---|---|---|
| `claude-opus-5` | 11 | 617,216 | 7,019 | $0.8792 |

---

## 3. Where the spend actually went

The per-request breakdown makes the shape of the spend obvious:

| timestamp | in | cache_r | cache_w | out | think | cost |
|---|---|---|---|---|---|---|
| 05:38:48 | 2 | 25,259 | 15,574 | 346 | 0 | $0.1770 |
| 05:38:52 | 2 | 40,833 | 4,072 | 378 | 36 | $0.0706 |
| 05:38:57 | 2 | 44,905 | 3,283 | 534 | 101 | $0.0686 |
| 05:39:07 | 2 | 48,188 | 4,668 | 1,020 | 431 | $0.0963 |
| 05:39:16 | 2 | 52,856 | 1,714 | 487 | 105 | $0.0558 |
| 05:39:24 | 2 | 54,570 | 4,096 | 484 | 199 | $0.0804 |
| 05:39:36 | 2 | 58,666 | 1,156 | 607 | 47 | $0.0561 |
| 05:39:50 | 2 | 59,822 | 936 | 367 | 75 | $0.0485 |
| 05:40:19 | 2 | 60,758 | 3,435 | 1,075 | 87 | $0.0916 |
| 05:40:41 | 2 | 64,193 | 1,372 | 1,183 | 370 | $0.0754 |
| 05:41:00 | 2 | 65,565 | 1,273 | 538 | 222 | $0.0590 |

**Findings:**

1. **Fresh input is 2 tokens per request — every time.** Literally everything else is
   served from cache. The CLAUDE.md context, the file reads, the conversation history:
   all cached. This matches the documented expectation in TOKEN_TRACKING.md.

2. **Cache reads grow monotonically, 25K → 65K.** That is the conversation
   accumulating. Each request re-reads the whole session at 0.1x the fresh rate. This
   is the single largest line item by token volume, but because of the 0.1x multiplier
   it is not the largest by cost per request.

3. **The first request is the most expensive single request of the session ($0.1770),
   and it produced almost nothing.** 15,574 cache-*write* tokens at the 1.25x
   multiplier — that is the session priming its cache with CLAUDE.md, the environment
   block, and the tool definitions. It is a fixed entry fee: ~20% of total session cost
   paid before any real work happened.

4. **Output is where the marginal cost lives.** The two priciest non-priming requests
   (05:39:07 at $0.0963 and 05:40:19 at $0.0916) are exactly the two with the highest
   output+thinking. Output bills at 25.00/M against 0.50/M for a cache read — 50x. A
   request that reads 60K cached tokens and writes 300 costs less than one that reads
   60K and writes 1,100.

5. **Reading four model files in one batched call was cheap.** The 05:39:24 request
   pulled all four model SQL files and cost $0.0804. Doing them as four sequential
   requests would have paid the growing cache-read cost four times over, for the same
   information.

### The practical lever

Input volume is not the thing to optimize here — it is 2 fresh tokens per request and
a 0.1x-billed cache read. **The lever is output tokens and request count.** Batching
independent reads into one request, and not re-deriving what is already established,
is what moves the number. Guardrails that stop the model from reasoning through files
it does not need (habit-hooks, pre-commit static analysis) attack the `out` and `think`
columns, which is the right target.

---

## 4. Work completed in the session

### Build result

```
dbt build --target dev
Done. PASS=37 WARN=0 ERROR=0 SKIP=0 NO-OP=0 REUSED=0 TOTAL=37
Finished running 3 table models, 33 data tests, 1 view model in 14.58s
```

Commands run: `dbt debug`, `dbt deps`, `dbt build --target dev`, plus direct
Snowflake queries to verify counts.

### Row counts by layer

| Layer | Object | Rows | Delta | Reason |
|---|---|---:|---:|---|
| Bronze | `ONLINE_RETAIL_RAW` | 541,909 | — | Untouched source |
| Silver | `stg_online_retail` (view) | 536,641 | −5,268 | Dedup of byte-identical repeat rows |
| Gold | `fct_revenue` (table) | 523,697 | −12,944 | Cancellations, write-offs, non-merchandise |
| Gold | `dim_customer` (table) | 4,372 | — | One row per identified customer |
| Gold | `dim_product` (table) | 4,054 | — | One row per merchandise stock code |

Every delta matches the figure already documented in the model YAML. No unexplained
movement.

### Silver flag distribution

| Flag | Rows |
|---|---:|
| `is_cancelled` | 9,251 |
| `is_return` | 1,336 |
| `not is_merchandise` | 2,940 |
| `not has_customer` (guest) | 135,037 |

Exclusions overlap; the union excluded from Gold is 12,944, matching `fct_revenue`'s
documented claim exactly.

### Gold sanity check

Total `extended_revenue` = **£10,247,219.32** across
2010-12-01 08:26 → 2011-12-09 12:50. Date range matches the documented dataset span.

---

## 5. One documentation defect found

`dbt/models/staging/schema.yml` describes `is_merchandise` as excluding
**2,946 rows**. The actual Silver count is **2,940**.

Not a logic bug — verified by running the same predicate against both layers:

- 2,946 = non-merchandise rows in **Bronze**, pre-dedup
- 2,940 = non-merchandise rows in **Silver**, post-dedup

Six of the non-merchandise rows are duplicates removed by the dedup step. The YAML
documents a Silver column but quotes the Bronze figure. The model is correct; the
comment is off by the dedup. Flagged, not fixed — it is outside the scope of
"execute the models."

---

## 6. Caveat on these numbers

The figures above exclude the final request of the session (the one writing this
file), because the transcript row is not flushed until after the request completes.
Expect the true session total to be modestly higher — one more request in the
$0.05–$0.10 band.

Costs are public list-price estimates, not an invoice. On a subscription they are a
relative signal for before/after comparison.

To reproduce:

```bash
.venv/bin/python -m src.scripts.token_usage 922dd7f8-7695-4d18-a1c4-5b02795796f9
.venv/bin/python -m src.scripts.token_usage 922dd7f8-7695-4d18-a1c4-5b02795796f9 --by-model
```
