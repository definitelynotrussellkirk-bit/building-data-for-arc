# Native forward/inverse analogy — owner acceptance pending

The old assessment deferred hidden parameters because they would change the
canonical task. This separate, opt-in native family makes that change explicit
without editing the production generator or the selected reference rule.

## Episode-fixed direction; instance-derived operator

`direction=forward` returns the selected canonical Racket source byte-for-byte.
It infers the exact-position support transformation from the first panel to the
second, aligns the first panel, learns the nonzero color map, and transfers the
inferred relation to the third panel. Unmapped query colors pass through.

`direction=inverse` learns that **same instance-specific relation**, but applies
its inverse geometry and inverse color permutation to the query. Quarter turns
swap direction; the other D4 operations are self-inverse. The native grammar
requires the demonstrated colors to form a bijective permutation, so this is a
real inverse on all colors, extending by identity to unmapped colors. A relation
with disjoint source/target palettes is deliberately outside this new grammar;
calling its pass-through extension an inverse would be incorrect.

The sequential dependency is essential to the original reasoning: A infers the
support transform and aligns panel 1 to panel 2; the aligned color correspondences
form an input-dependent intermediate; B constructs/transfers the forward or
inverse operator to panel 3. The wrong-order witness tries to learn colors before
alignment. On the retained example the original and aligned supports are
disjoint, so that shortcut cannot recover the color cycle and changes six cells.

The adapter loads this task's existing geometric helpers by exact adjacent path.
The base generator and canonical ledger remain unchanged. Python outputs are
claims; native qualification and the audit independently execute protected Racket.
All setting and counterfactual programs are tested as one complete expression.

## Grammar and curriculum

Three panels of equal width 4..9 and height 4..30 are separated by color-5 columns.
An optional final color-5 divider is permitted. Square panels support all eight
exact-position D4 transforms; rectangular panels use the shape-preserving subset.
Examples uniquely determine their support transform and a permutation of at least
three nonzero colors. Color 5 is reserved for separators in this new sampler.
Queries mix demonstrated colors and an unmapped color, which must pass through.

Two constructive demos teach the hidden direction. The first uses a clockwise
relation with tied color frequencies; the second uses a reflection and reverses
the numeric order of the color cycle. Their query supports have full exact-D4
uniqueness. Together they reject fixed geometry, histogram matching, dropping
unmapped colors, numeric color cycles and learning the map before alignment.
Additional demos and queries vary geometry, positions, palette, permutation
arity, occupancy and size. No arbitrary holdout-rotation guarantee is claimed.

Requests support exact integer seeds 0..2**63-1, 2–6 demos, and 1–4 independent,
prefix-stable queries. Ordinary qualification uses three demos and four queries.
Inputs do not receive the hidden setting. Query sizes are 4x14, 7x23, 9x29 and
30x30. The last consists of three real 30x9 panels plus three separator columns:
108+108+94 foreground panel cells and 90 divider cells, not a padded small puzzle.
Its output is **30x9**, with all four output corners occupied. The final divider
is ignored by the unchanged canonical split formula; this is an explicit new
native layout, not a claim that the original square-only production sampler
supports 30x30.

Panel construction has a bounded 32-attempt exact-support search and a small
asymmetric fallback for ordinary panels. Failure is explicit; a finite sweep is
not a guarantee for every seed. Structured teaching profiles, finite policies,
and authored causal interpretation remain limitations, not universal uniqueness
or measured learning benefit.

## Public projection and replay

`public_turn(episode,index)` whitelists demonstration input/output and one query
input. It excludes private metadata even when injected into demonstration pairs.
Settings, programs, query answers, future inputs and total-query hints are private.
The same first-turn bytes are used with one or four stored queries. `audit.py`
writes hash-named public files through `reviewer_support.public_challenge_bytes`.

From the outer packet directory:

```sh
python3 review.py run python3 -m pytest -q generators/155cf6b30713/tests
python3 review.py run python3 generators/155cf6b30713/workspace/parametric/audit.py --seeds 32 --out ../checks/155cf6b30713/audit-fresh
python3 WORK/check_public_exports.py WORK/checks/155cf6b30713/audit-fresh/public --queries 1 --demos 3 --summary
python3 review.py run python3 -m arcpuzzles parametric qualify 155cf6b30713 --seed 0 --seed 17 --demos 3 --queries 4 --timeout 60 --out ../checks/155cf6b30713/qualification-fresh --summary
```

`audit.py` includes a **deliberately weak lesson** negative control: two clockwise
examples admit a constant counterclockwise-transfer shortcut, while the actual
second reflection demo rejects it. This is not reported as a production defect.
The native manifest and qualification bind exact source; the separate causal
witness records protected execution and replay. Owner acceptance remains a
separate action and no training admission is granted.
