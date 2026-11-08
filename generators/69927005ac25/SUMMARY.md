# 69927005ac25 — Diagonal Midpoint Completion

For every pair of equal nonzero cells separated by `(2, 2)` or `(2, -2)`, fill the diagonal midpoint with that color. All matches in one pass are detected from the same source grid, so newly written cells do not trigger further writes until a later pass.

The repaired base generator honors exact dimensions and pair-count aliases, validates diagonal construction, avoids endpoint/midpoint collisions, and rejects unknown or conflicting overrides.

The task-local parametric family has two settings:

- `passes: 1`: the byte-exact canonical one-pass program.
- `passes: 2`: apply the same simultaneous-source rule exactly twice.

Teaching scenes contain causal cascades for which one pass, two passes, and transitive closure are all different, plus axis-aligned, already-complete, and distance-four decoys. Both settings support 2–6 demonstrations and exactly four independent queries, including a lawful 30×30 stress case.
