# Native directional-paint family

This family preserves the exact canonical `fixed_right` program and adds two
nearby episode-fixed settings:

- `fixed_left`: every original red source paints one cell left.
- `anchor_inward`: **Step A** compares red counts on the left and right borders
  and derives the strict-minority border as `anchor_side`; **Step B** consumes
  that side and paints every original red source one cell inward.

The sampler uses matched inputs across settings, supports 2–6 prefix-stable
demonstrations and 1–4 prefix-stable queries, includes adjacent red sources to
retain source-before-write semantics, and uses a substantive 30×30 fourth query.
The first two demonstrations have opposite border minorities, which identifies
all three declared settings from labels alone. `prototype.py` remains as the
older two-setting research record; native qualification uses `adapter.py` and
`native_family.py`.

## Reproducible audit

`audit_native.py --seed-count 32` exercises every supported demonstration and
query prefix, verifies matched inputs and prefix stability, checks every public
turn for private-answer leakage, and evaluates all declared finite rivals. The
checked report is retained at `evidence/current/audit.json` and is bound to the
exact `native_family.py` SHA-256 recorded in that report.
