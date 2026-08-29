# AI Review Checklist

Six checks, applied to every AI-authored change before it is accepted. They are ordered
by how often they catch something on this dataset.

This is a reviewer's tool, not a slide. **Don't screen-share it before Beat 3** — it
names quirks the audience should watch Cortex discover for itself.

The checklist assumes the layer rules in `CLAUDE.md` and the vocabulary in `AGENTS.md`.
It is not a substitute for reading the diff; it is what you read the diff *for*.

---

## 1. Is this a rule, or a pattern that happened to fit?

The most expensive failure mode on this dataset, and the one that looks most like
competence.

A rule holds across the data. A pattern holds across the rows someone happened to look
at. They produce identical-looking SQL and wildly different revenue numbers.

**Ask:** what rows satisfy the *intent* of this predicate but not the predicate itself?
Then run that query. Don't reason about it — run it.

**Where it bites here:**

- `InvoiceNo` prefixes are a convention, not a contract. A filter built on one observed
  prefix will pass every test written by the same author and still leak.
- `StockCode` is case-inconsistent — `15056BL` and `15056bl` are one product wearing two
  identities. Any join, group-by, or dedup keyed on raw `StockCode` splits them.
- `Description` is free text and unreliable as a classifier. A rule that reads
  descriptions to decide what a row *is* will drift the moment the text does.

**Reject if:** the predicate was written before any query was run against the column it
keys on.

---

## 2. Do the `not_null` tests describe reality, or the author's assumption?

A test that fails on correct data teaches the team to ignore failures. That is worse
than having no test, because it degrades every other test around it.

**Ask:** what is the actual null rate of this column? Was it measured, or assumed from
the column's name?

**Where it bites here:**

- `CustomerID` is null in roughly a quarter of all rows. These are guest checkouts —
  genuine, valid transactions, not corrupt records. `not_null` on `CustomerID` in Silver
  is simply wrong, and "fixing the data" to satisfy it deletes a quarter of the business.
- `Description` is missing on a meaningful minority of rows, mostly on adjustment and
  fee lines rather than products.
- Conversely: a column that genuinely is never null and has *no* test is the other half
  of this check. Absence of a bad test is not presence of a good one.

**Reject if:** a `not_null` was added without the null-rate query, in either direction.

---

## 3. Does the fix generalize, or does it patch the instance in front of us?

The tell is a fix whose shape matches the example rather than the cause — a specific
value excluded, a magic number, a hardcoded identifier, a `WHERE ... <> '<the row that
broke>'`.

**Ask:** if a second row with the same underlying problem arrived tomorrow, would this
change catch it? If the answer needs a caveat, it's a patch.

**Where it bites here:**

- Excluding one adjustment row by its exact value or identifier, rather than
  understanding what class of row it belongs to and excluding the class.
- Handling negative `Quantity` and negative `UnitPrice` as two unrelated problems, when
  both are symptoms of "this row is not a sale."
- Casting `CustomerID` by stripping a literal `.0` suffix, rather than treating it as
  the Excel float-coercion artifact it is and casting through a numeric type.

**Reject if:** the change would need editing again for the next instance of the same
problem.

---

## 4. Is every row-count delta explained — including the ones that look right?

Row counts are the cheapest lie detector in a pipeline, and the discipline only works if
it is applied when the number looks *good*. A drop that matches your expectation is the
one you don't investigate.

**Ask:** before, after, delta, and the reason. Three numbers and a sentence. Does the
sentence account for the whole delta, or most of it?

**Where it bites here:**

- Bronze must be exactly the source row count. Not approximately. If Bronze lost rows,
  something cleaned, and Bronze does not clean.
- Silver's dedup removes a specific, countable set of exact duplicate rows. That count
  should be stated and stable across runs. "Some duplicates" is not a number.
- Gold's exclusions each account for a named slice — cancellations, returns,
  non-merchandise, adjustments. If the excluded total exceeds the sum of the named
  slices, something is being dropped that nobody has named, and that residual is where
  the bug is.

**Reject if:** the delta is stated without a reason, or the reason covers only part of it.

---

## 5. Are the non-obvious categories handled explicitly, or by silence?

Some rows in this dataset are not products, not sales, and not errors. They are real
business events that a naive aggregation quietly swallows.

**Ask:** for each category below — is it handled by a named, tested decision, or does it
just happen to fall out of some other filter? Falling out is not handling. It works
until the other filter changes.

**Where it bites here:**

- **Non-merchandise `StockCode`s** — postage, carriage, bank charges, manual
  adjustments, gift vouchers, marketplace fees. Dozens of distinct codes sharing a
  column with real products. They inflate product counts and distort revenue-per-item.
- **Adjustment rows** carrying large negative amounts, which can offset a meaningful
  fraction of a month's revenue if included, and distort it if excluded silently.
- **Returns** — negative quantity against a prior sale. A legitimate business event with
  a defensible argument for inclusion *and* for exclusion. Either is acceptable; being
  unable to say which was chosen is not.
- **Guest checkouts** — no `CustomerID`. Fine in a revenue fact, fatal in a
  customer-level aggregate that silently drops them.

**Reject if:** you cannot point at the line of code, or the YAML sentence, where the
category was decided.

---

## 6. Would you accept this from a junior engineer on your team?

The one that catches everything the other five miss — because the honest answer arrives
before the justification does.

Not "is it impressive," and not "is it wrong." The question is whether you'd merge it,
and whether you'd be comfortable when it produced a number someone acted on.

**Ask:**

- Can I tell what this does without asking the author?
- Are the decisions written down where the next person will find them — in the YAML
  description, not in a chat log?
- Was it run, or only written? Does the author say which?
- If this number were wrong, how would anyone find out?
- Does the confidence in the write-up match the evidence behind it?

**Reject if:** you'd hold a person to a standard this change doesn't meet. The author
being a model is not a reason to lower the bar — it is the reason the bar has to be
explicit.

---

## Applying it live

You will not run six checks on stage in the time available. Pick by layer:

| Change touches | Run checks |
|---|---|
| Bronze loader | 4, 6 |
| Silver model | 1, 2, 4 |
| Gold mart | 1, 3, 5 |
| A one-shot end-to-end build | 1, 4, 5 — in that order |

Check 1 first, always. Everything downstream inherits it.
