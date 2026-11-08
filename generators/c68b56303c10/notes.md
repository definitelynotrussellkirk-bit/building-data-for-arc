# c68b56303c10 — current decisions

## Rule and authority

Take the bounding box of all red/color-2 cells and that of all green/color-3
cells, intersect their inclusive row and column intervals, and output a solid
color-8 grid with the intersection's height and width. The canonical Racket
program is unchanged; normalized `RULE_HASH` is `42cdb52c8cce`. Colors 2, 3 and 8
have fixed meanings. The two input-color roles may be exchanged because bbox
intersection is symmetric; arbitrary palette permutations are not lawful.

## Current sampler, version 3.0.0

Geometry is chosen before colored points. Both color boxes are realized with
varied extremal edge points and exact disjoint cell allocation. The bounded
random placement phase has a constructive balanced-crossing fallback; it does
not silently shorten counts or replace a failed requested shape. Every band
supports exact `grid_h=7..18`, `grid_w=8..22`, and `n_red,n_green=2..8` overrides.
Unknown axes and Boolean, float, or string values for integer overrides fail
explicitly; `None` leaves the axis unset. Difficulty changes point-count weights;
admissible control ranges and the mathematical rule remain the same.

Each draw favors a jointly selected canonical canvas anchor from 8x10, 9x11,
10x12 and 11x13, while retaining every advertised height and width. Large canvases
remain available, but no band requires them. Canvas and geometry ranges remain
available in every band; drawn counts can also affect the separator's count-tuple
exclusion and subsequent point placement. Identical seed/index calls can coincide
across bands; deduplicate inputs when combining bands.

The period-2 teaching schedule alternates:

- `separator`: a wide overlap of width at least four, with both green
  bbox starts/ends before the red ones, variable green protrusion, and output
  dimensions different from the red/green count tuple. It refutes all nine
  declared rivals in a single example.
- `coverage`: overlap dimensions anywhere in 1..(canvas dimension-2), with extra
  weight on canonical output sizes 2x2, 4x3 and 5x3. Relative bbox intervals vary
  freely, including containment, equality, mixed directions and thin overlaps.

With three demonstrations plus one query, every four consecutive raw draws
contain two separating examples. Thus each single-query holdout still retains a
separating demonstration. Production acceptance/deduplication can change raw
indices, so actual accepted lessons and rotations were also checked with the
shared Racket-backed census. `lesson_identifiable` tests only the declared rival
set; it does not assert uniqueness against every possible program.

## Reversals and why

The prior v2.1.1 scattered-point sampler grew both bboxes with canvas size and
point count. The retained lead was `review-2421806ec3b8287f:v0001`, source
`100f77410cfc8619c192150065c03d2abee9e1eac2fb12c7330319150a271e16`.
A fresh seed-10007, index-0..199 census reproduced hard output medians 9x11 and
0/200 canonical output-size hits. Constructing the overlap first restores
60/200 canonical output-size hits in each band and hard medians 4x5 in the same
population. Canonical input-profile hits rise from 0/200 hard to 123/200; every
band has 133/200 canonical-envelope hits. These are input-geometry diagnostics;
authoritative Racket checks and lesson evidence are retained separately.

Unused palette/density/position aliases and publicly advertised invalid textures
were removed. They were never real curriculum variation. Negative/malformed
inputs belong in tests, not in ordinary generation. Canonical inputs now pass
validation regardless of a difficulty label.

An intermediate overlap pool restricted separating examples to height <=3 and
width <=6. Strict lint reported only 28 distinct outputs in 144 pairs. That
restriction was reversed: both profiles now use their full feasible geometric
ranges. Final lint observed 60 distinct outputs in 144 pairs, with zero errors
and warnings. No finite-output-codomain exemption was declared: the output color
alphabet {8} is not the alphabet of possible output grids.

## Validation scope and limits

`self_check` and `strict_canonical_like` validate the mathematical domain and
literal cell types, not complete membership in the narrower sampling support.
They may accept lawful 1..30 grids with one point or more than eight points of a
color. Generated draws still obey all four exact controls and sampled invariants.
This is deliberate: difficulty and curriculum weights must not make lawful
canonical inputs invalid. A returned strict fraction is a semantic-domain
measure; canonical size/palette support is measured separately.

Normal generation is restricted to background 0 and fixed colors 2/3, at least
two points per color, two-dimensional bboxes, and overlaps leaving room for
proper crossings. It is not exhaustive over all grids on which the Racket rule
can execute. Sparse edge supports, a period-2 lesson structure and canonical
shape weighting are distribution choices, not universal ARC properties.

## Evidence and open findings

Task-local tests cover all canonical pairs in every band, exact controls and
joint endpoints, invalid scalar/cell types, profile floors, canonical-fitting
rivals, minimal counterexamples, and short lesson rotations. The reusable
`workspace/probe_distribution.py` writes hash-bound before/after diagnostics.
`counterexamples/canonical_shortcuts.json` retains two small examples separating
all four canonical-fitting rivals from the intended rule.

Final source SHA256:
`7de0c2fe4b3b7e584afd491601ebe31a755cade9a1bf19c4d11e6eedfd6b4194`.
The final 300-lesson census materialized 1,200 distinct inputs and tested 1,200
query rotations with no ambiguity, scoring error or hook warning against nine
unique rivals. Fixed-seed enumeration covered both start residues in all three
bands: six lessons, 24 rotations, 13 unique inputs. These finite results do not
establish universal identifiability, Qwen learning gains or training admission.

The existing audit index is preserved. This repair addresses its dead-control
and scale concerns with new evidence; maintainer disposition of that retained
audit is still explicit, rather than inferred from changed source bytes.
## Current reviewer considerations

Source SHA-256: `7de0c2fe4b3b7e584afd491601ebe31a755cade9a1bf19c4d11e6eedfd6b4194`.

# Decisions — c68b56303c10

Final generator: version 3.0.0, SHA256
`7de0c2fe4b3b7e584afd491601ebe31a755cade9a1bf19c4d11e6eedfd6b4194`.
Canonical Racket rule `42cdb52c8cce` and canonical ledger are unchanged.

## D1 — Choose overlap geometry before scattering points

**Prior choice/rationale:** the original sampler placed red/green points uniformly
on a canvas, then retried when their boxes did not intersect. The specific reason
for its difficulty-dependent size/count escalation is unknown; its code comments
favored wider output variation. More points across larger canvases make large
box intersections common, regardless of canonical output scale.

**New choice:** draw a target overlap, choose two realizing bbox interval pairs,
then allocate disjoint extremal/support cells. Distinct colors cannot overwrite
one another. Exclusive/shared-cell capacity is checked before sampling fills;
a balanced-crossing fallback covers the full advertised integer-control domain.

**Alternatives rejected:** lowering hard canvas sizes alone would preserve a
canvas-to-answer correlation; increasing rejection limits would not fix that
bias; hardcoding canonical inputs or replaying a fixed small set would shrink
useful input diversity. Evidence: `checks/distribution-before.json`,
`checks/distribution-final.json`, and the selected tests.

## D2 — Canonical support is a mixture in every band

**Prior choice:** easy, medium and hard had disjoint or weakly overlapping count
and size domains. Canonical three-red/three-green inputs were rejected as hard.

**New choice:** four meaningful exact integer controls share one global domain.
A jointly selected canonical anchor supplies extra weight to canvas dimensions,
but every advertised endpoint remains selectable. Difficulty changes default
point-count weights only. Coverage-profile overlap shapes include every feasible
height/width and weight 2x2, 4x3 and 5x3, preserving canonical output-size mass.

The seed-10007, 200-draw-per-band diagnostic found 123/200 exact input profiles,
133/200 envelope hits and 60/200 canonical output shapes in every final band.
There are 200 unique inputs within each band, 460 across the 600 pooled draws;
shared seed/index can yield the same input across bands. These are not 600 unique
training examples. The separate random lesson census has 1,200 unique inputs.

## D3 — Remove controls that never controlled observable input properties

**Prior choice/rationale:** palette_kind, palette_size, n_distinct_colors, density,
position_bias and texture were advertised even though colors are rule-fixed;
the original rationale is unknown. Some were silently ignored and negative
textures bypassed ordinary invariants and dimension overrides.

**New choice:** advertise only grid_h, grid_w, n_red and n_green; report all four
from returned pixels through `observe_overrides`. Reject unknown keys and bool,
float and string integer values. Do not invent palette semantics or alter the
fixed Racket colors to make obsolete controls appear active. Negative cases are
retained in tests rather than exported as normal valid samples.

Evidence: `checks/regression-before.log`, `checks/semantic-regressions-before.log`,
`checks/focused-after-v3.log`, and final task-test/override receipts.

## D4 — Teach the distinctions that canonical examples leave unresolved

All four labeled canonical pairs fit four wrong rules: directed red-bottom/right
minus green-top/left, sorted tall output dimensions, width capped at three, and
green bbox width minus three. Two minimal canonical-scale changes distinguish
these rivals; selected Racket execution verifies their outputs.

**New choice:** nine pure executable rivals and four paired witnesses, including
all four verified canonical-fitting shortcuts. A period-2 schedule alternates a
strong separating draw and a broad coverage draw. For three demonstrations and
one query, every four consecutive raw draws contain two separators, so any
single-query holdout retains one. The hook reports only a rival that fits every
demonstration and changes the query, not a rival that also agrees on the query.

**Alternatives rejected:** occasional random counterexamples can miss a short
lesson; a single special demonstration disappears if held out; assuming three
examples teach an arbitrary mapping ignores the exact d552baa9e49e audit witness.

**Executed policy:** ordinary production sampling, three demonstrations and one
query, plus all four query rotations. Final source-bound census:
`checks/lesson-census-final.compression.json` and its `.summary.json`; 100 lessons
per band, 300 materialized lessons, 1,200 distinct inputs, 1,200 rotations, zero
ambiguity/errors/warnings against nine unique rivals. Separate fixed-seed
schedule census: `checks/schedule-census-final.json`, start residues 0 and 1,
seed 0, all three bands, six lessons/24 rotations/13 unique inputs. This does not
exhaust seeds, arbitrary demonstration subsampling or undeclared rivals.

## D5 — Widen the first repair after a real lint warning

The first implementation limited separators to overlaps no taller than three
and no wider than six. Its 68 focused tests and 300-lesson census passed, but the
strict battery reported low output diversity: 28 distinct output grids in 144
pairs. That was an introduced distribution restriction, retained in
`checks/after/` and `checks/distribution-after.json` as intermediate evidence.

The final sampler uses all feasible wide separator dimensions and the full
coverage dimension grid. It preserves canonical weighting and redundant rival
refutations. Lint now sees 60/144 distinct outputs (42%), with zero warnings.
A missing closing bracket in the initial code draft is separately retained in
`checks/focused-after-v1.log`; the corrected first geometry passes at v2, and
expanded geometry at v3. These failed development checks are not solve attempts.

## D6 — Keep semantic validation separate from sampler membership

`self_check` enforces rectangular literal integer grids, rule-fixed colors,
presence of both colors and a positive overlap. It intentionally accepts lawful
inputs outside the narrower sampled size/count ranges. Canonical validation must
not depend on difficulty. Exact requested counts and canvas sizes are enforced
by construction, public observations and focused endpoint tests.

This distinction is documented rather than silently treating every semantic
validation pass as coverage of the sampler. The broad canonical-like hook is a
rule-domain check, not a claim that every accepted grid is likely or sampled.

## D7 — Retain local tools and source-bound findings

`repo/generators/c68b56303c10/workspace/probe_distribution.py` replaces ad hoc before/after geometry counting
with a reusable, no-overwrite JSON report carrying source/data hashes, seeds,
profiles, exact counts and uniqueness. It computes input-derived diagnostic
shapes; it never relabels data or substitutes for the Racket authority. Audit
reproducers stay with their own targets under `checks/audit/`; neither audited
source was modified. The inherited audit index and its explicit unresolved
status remain intact for maintainer disposition.

## Self-review and practical limits

The repair introduces a deliberate repeated-counterexample lesson mixture and
retains a narrower sampling support than the full Racket domain; the final
expanded geometry, joint-control tests, independent fallback probe and accepted
lesson census check the concrete shortcuts this could create. Finite rival
success and profile support do not establish universal induction or improved
Qwen performance, and neither Python solve's masked query correctness was
revealed to the reviewer.
