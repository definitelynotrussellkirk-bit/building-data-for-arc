# Native size-rank and dominant-axis family

The native family preserves the exact canonical `small_to_large` program and
adds two nearby settings:

- `large_to_small`: reverse the size ranking before assigning interior colors.
- `dominant_axis`: **Step A** compares doubled rectangle-center separations and
  derives `row` or `column`; **Step B** consumes that axis to order the two
  rectangles along it, then applies the canonical interior recoloring with 1
  for the first object and 2 for the second.

Inputs are matched across settings. The sampler supports 2–6 prefix-stable
demonstrations and 1–4 prefix-stable queries. Its first three demonstrations
separate size order, fixed row order, fixed column order, reverse-axis order,
and the declared dominant-axis rule. The fourth query is a 30×30 case whose two
large rectangles contain 378 nonzero cells and touch all four canvas boundaries.
`prototype.py` remains as the older two-setting research record; native
qualification uses `adapter.py` and `native_family.py`.

Seed variation uses a joint translation of both rectangles, preserving every
row/column ordering relation rather than silently reflecting a rival rule into
or out of agreement. The first two demonstrations distinguish the three
settings; aliases that remain observationally equivalent on those labels are
constructed to remain equivalent on all four independent queries.

## Reproducible audit

`audit_native.py --seed-count 32` exercises every supported demonstration and
query prefix, verifies matched inputs and prefix stability, checks every public
turn for private-answer leakage, and evaluates all declared finite rivals. The
checked report is retained at `evidence/current/audit.json` and is bound to the
exact `native_family.py` SHA-256 recorded in that report.
