# `b5b012cd97d9` parametric prototype

This prototype keeps the catalog-selected count-and-pack program as the exact
`canonical` default and adds one input-dependent setting, `preserve_vertical`.

1. **Step A — derive an intermediate.** Count colors exactly as the canonical
   rule does, identify the large and small repeated roles, compute their
   bounding boxes, and set `big_above` from their doubled row centers.
2. **Step B — consume the intermediate.** Build the canonical packed answer.
   Leave it unchanged when `big_above` is true; rotate it 180 degrees when it
   is false. The output therefore preserves whether the large role was above
   or below the small role in the input.

The first two demonstrations deliberately exercise `big_above = true` and
`false`, so the minimum two-example lesson separates the declared settings and
fixed/reversed shortcut rules. Sampling is deterministic and keyed by
`(seed, split, index, purpose)`, which keeps demonstration and query prefixes
stable as requested counts change. Query four is a dense 30×30 boundary stress
case whose exact counts still satisfy the source rule.

`adapter.py` exports only the native `program(settings)` and
`generate(seed, settings, demos, queries)` entry points. Public projection
helpers emit demonstration inputs/outputs and query inputs only; settings,
programs, future queries, and query answers remain private.
