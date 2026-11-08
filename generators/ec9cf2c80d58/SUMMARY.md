# ec9cf2c80d58 — colored bands and original-input extents

Selected generator version: **4.0.0**. Kind: `per_puzzle`.
The canonical Racket rule remains the label authority, with rule hash
`899eb4e6a25d`. Python rule and rival functions support authoring checks only.

For each zero hole in the **original input**, select the first nonzero neighbor
in UP, DOWN, LEFT, RIGHT order. Call its color C. Count every C-or-zero cell in
the hole's complete row and complete column, including zeros in other bands.
If row count is greater than or equal to column count, erase the C-or-zero cells
in that column; otherwise erase them in that row. **Ties clear the column.**
Combine all erasures while reading every decision from the original input.
Band orientation alone does not determine the branch.

## Structure and exact controls

Inputs have two to five contiguous bands of distinct nonzero colors, each at
least two cells thick. Every row/column along the band axis retains its band's
color. There is at least one hole, and its selected neighbor has its latent band
color. Bands may be inactive; lawful edge holes are allowed. The structural
validator accepts all ten labeled pairs in the two canonical ledger variants.

| Independent axis | Exact accepted values |
|---|---|
| `grid_h` | Final grid height, integer 6..24 |
| `grid_w` | Final grid width, integer 6..24 |
| `orientation` | `horizontal` or `vertical` |
| `n_bands` | Integer 2..5 |

`palette_size` and `n_distinct_colors` are supported **compatibility aliases**,
each in 3..6 and each equal to `n_bands + 1`, **including zero**. They are not
additional independent axes. Supplied controls must agree; band thickness must
fit the requested orientation and final dimensions. Numeric controls reject
booleans, strings and coerced values. Unknown controls, including the old
`palette_kind`, `position_bias`, and `texture`, now fail loudly. Contradictory
legal controls raise `ValueError` with `incompatible_axes` naming supplied keys;
shape conflicts provide context rather than a guaranteed minimal conflict set.

## Default lesson schedule

The period-eight schedule is canonical-horizontal, teaching,
general-horizontal, teaching, canonical-vertical, teaching, general-vertical,
teaching. Canonical profiles retain the five canonical shape/palette combinations
across every difficulty. General profiles vary aspect ratio, partitions, band
counts, active bands and holes. Difficulty biases general band-count preference
without shrinking the legal override domain.

Teaching uses two equal vertical bands: `m=7..10`, height `m+1`, width `2m`,
with holes `(p,q)`, `(p+1,q)`, `(p,m+k)`, where `p=1..m-2` and `q,k=0..m-1`.
Optional left/right reflection preserves the selected-neighbor invariant. Each
teaching input refutes all six declared rivals: perpendicular erasure, excluding
zeros from extents, sequential updates, row-clearing ties, always row, and always
column. Every four consecutive default examples contain two teaching examples,
so three demonstrations retain at least one under any query rotation.

This guarantee is finite and applies to **default, unoverridden lessons** with
three demonstrations and one query. Explicit overrides use the general sampler
and are outside that lesson guarantee. Teaching occupies half the schedule;
the scheduled mixture is **75% vertical and 25% horizontal**. Its recognizable
teaching geometry leaves possible shape-dependent shortcuts beyond the six
declared rivals. No universal identifiability claim is made.

## Retained evidence

[`notes.md`](notes.md) gives the repair rationale and teaching derivation.
[`workspace/README.md`](workspace/README.md) describes reproduction.
The two compact JSON counterexamples retain authoritative Racket outputs and
separate Python rival outputs. The tiny combined 3x4 fixture is not emitted by
the default generator; scaled teaching examples are.

`WORK/checks/extents-probe-final.json` records **37/37 valid Racket executions**
with no Python-model mismatch: three tiny fixtures, ten canonical pairs and
twenty-four generated examples. Its exhaustive **3,992** teaching geometries are
checked using Python and an independent closed form, **not** per-grid Racket.
The final battery passes all twelve stages without advisories, and all 42
task-local regressions pass. The final lesson census materializes 300 lessons
(100 per difficulty), with 1,200 unique inputs and zero declared-rival ambiguity
in both 300 production assessments and 1,200 query rotations. A separate
seed-zero period-eight census covers 24 overlapping lessons and 96 rotations
over 11 unique inputs, also without ambiguity. These source-bound results are
retained in `WORK/checks/after-final/`, `WORK/checks/task-tests-final-v2/`,
`WORK/checks/lesson-census-final.json`, and
`WORK/checks/schedule-census-final.json`. Catalog approval and training admission
remain separate from these authoring and verification receipts.
