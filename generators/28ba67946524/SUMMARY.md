# 28ba67946524 — Highlight Distance-Two Components

Version 3.1.0. Canonical Racket rule hash remains `88eede4e9a69`.
A unique blue component seeds the four-neighbor contact graph of same-color
components. Recolor **all and only** components at shortest graph distance two
with 8 on an otherwise zero canvas.

The deterministic period-2 sampler alternates randomized paths and branched
four-cycles. The branch now contains a seed-adjacent triangle: one endpoint is
reachable by a two-edge walk but has shortest distance one. This preserves both
true distance-two targets while refuting the canonical-fitting shortcut “paint
all endpoints of any two-edge walk.” Shapes, sizes, placements, orientations,
palettes, input color 8, and disconnected objects vary.

Odd-index examples refute all eight declared rivals. Four rivals fit every
canonical pair: fixed color 4, first target only, merge equal-colored components,
and the new two-edge-walk shortcut. Every three consecutive examples includes a
branch witness; every four-pair pool contains two, so a single arbitrary holdout
leaves a witness in three demonstrations. This is finite declared-rival teaching
support, not universal identifiability.

All four exact controls remain honored across every difficulty band.
`chain_len` is maximum reachable graph distance and `n_distractors` is the count
of disconnected components. The minimum 8×10 canvas supports distance 6 and
four distractors. Generation constructs inputs only; authoritative labels remain
Racket-owned. `LESSON_SCHEDULE_PERIOD=2` permits exact schedule enumeration.
