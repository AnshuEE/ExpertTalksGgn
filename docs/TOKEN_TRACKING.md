# Token Tracking: Measuring API Spend Per Request

Track input/output token spend and estimated cost for every Claude Code API request. Verify that guardrails (habit-hooks, pre-commit checks) actually reduce spend.

## TL;DR

```bash
# All sessions for this project
.venv/bin/python -m src.scripts.token_usage

# Per-request breakdown for one session
.venv/bin/python -m src.scripts.token_usage <session-id>

# Group totals by model (opus vs haiku)
.venv/bin/python -m src.scripts.token_usage <session-id> --by-model
```

## Where Data Comes From

Claude Code writes session transcripts to `~/.claude/projects/<slug>/<session-id>.jsonl` — one JSON object per line. Each `assistant` row carries `message.usage` with:

- **Fresh tokens:** `input_tokens`, `output_tokens`, `thinking_tokens`
- **Cache reads:** `cache_read_input_tokens` (billed at 0.1x)
- **Cache writes:** split into `ephemeral_5m_input_tokens` (1.25x) and `ephemeral_1h_input_tokens` (2.0x)

## Output Explained

### Session listing (default)
```
session                             when                reqs      in       out      cost
384391a9-c7fe-4a48-8d40-9d6f74e1140b   2026-10-08 12:44   18   2,902,726  16,950 $3.3913
```
- `in`: billable input (fresh + cache reads + cache writes)
- `out`: output tokens
- `cost`: estimated USD at list prices

### Per-request breakdown (`<session-id>`)
```
timestamp             model                   in  cache_r cache_w  out think    cost
2026-10-08T12:49:59   claude-opus-5           2   182,206   1,090 1,596   460 $0.1248
```
Shows per-model pricing and separate cache columns—revealing that your input is nearly all cached.

### By model (`--by-model`)
```
model                      reqs   in(billable)    out      cost
claude-opus-5               13      2,478,003  13,989 $3.2275
claude-haiku-4-5-20251001    6        627,347   3,183 $0.2777
```

## Key Numbers to Know

| Concept | What It Means |
|---------|---------------|
| Billable input | `input_tokens + cache_read_tokens + cache_write_tokens` |
| Cache read | Served from cache, **billed at 0.1x** fresh input rate |
| Cache write 5m | Short-lived cache, **billed at 1.25x** fresh input rate |
| Cache write 1h | Long-lived cache, **billed at 2.0x** fresh input rate |
| Output tokens | 5–50x more expensive than input depending on model |
| Thinking tokens | Part of output, only on models with extended thinking |

**On your pipeline:** Fresh input ≈2 tokens/request. Cache reads ≈190K tokens/request. Output is where your spend actually lives.

## Measuring Cost Savings (Before/After Habit-Hooks)

1. **Baseline:** Run your workflow *without* `.habit-hooks/` active (e.g., rename `.habit-hooks/` temporarily).
   ```bash
   mv .habit-hooks .habit-hooks.off
   # Run your workflow (e.g., `dbt build` or code review)
   .venv/bin/python -m src.scripts.token_usage | head -2  # note the cost
   ```

2. **With hooks:** Re-enable and run the *identical* workflow.
   ```bash
   mv .habit-hooks.off .habit-hooks
   # Run the same workflow
   .venv/bin/python -m src.scripts.token_usage | head -2  # compare cost
   ```

3. **The delta is your savings.** Static analysis (unused imports, swallowed exceptions) saves Claude reasoning through files, which is output-heavy. Watch the `out` and `think` columns, not `in`.

## Implementation Notes

### Deduplication
One API request emits *several* transcript rows (one per content block). The script deduplicates on `requestId` so each request is counted once. Counting rows instead would inflate numbers ~2.7x.

### Per-Model Pricing
Model IDs arrive in multiple spellings (`claude-opus-5`, `claude-opus-5[1m]`, `claude-haiku-4-5-20251001`). The script uses longest-prefix matching to resolve rates correctly. Unknown models print `n/a` rather than guessing.

### List-Price Estimates
Costs are public API rates, not an invoice. On a Claude subscription, they're a relative signal for before/after comparison, not an exact bill. Update `RATES` in the script if prices change.

## Testing

```bash
pytest tests/test_token_usage.py -v
```

14 tests verify deduplication, per-model pricing, cache multipliers, and edge cases.

## For Next Steps

- **Compare two sessions:** Add `--compare <session-a> <session-b>` to show the delta automatically
- **Live tracking:** Extend the script to write a running `.tsv` log so you can `tail -f` costs during long workflows
- **Threshold alerts:** Flag when a session exceeds a cost budget (e.g., `--max-cost 5.00`)
