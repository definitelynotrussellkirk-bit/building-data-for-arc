# dfa5c1702b4c — current generator decisions

## Rule and domain

Version 3.0.1 pins the unchanged canonical Racket rule `5264524f1c03`.
Final generator SHA-256: `0ba5665018235581095d844bd1ad759c0ee30fb5b9d36c4602bf5c45d130fd4e`.
Extract 2–7 distinct-color solid rectangles on background 0, sort by bounding-box
(top, left), and compare inclusive row and column projections. Codes are
0/neither, 1/rows, 2/columns, 3/both. Rectangles have a one-cell Chebyshev moat.
All five labeled canonical inputs belong to this domain. Off-diagonal 3 is
impossible for disjoint solid rectangles and is not a missing required branch.
Interlocking shapes, repeated colors, and touching objects are outside this sampler.

## Repairs and reversals

- The original sampler advertised controls it never consumed. `grid_h` 10–20,
  `grid_w` 11–20, and `n_distinct_colors` 2–7 now use actual keyed draws and are
  recovered by `observe_overrides`. All 660 legal joint combinations are
  constructive. Failed random placement cannot silently reduce the object count.
  Integers are strict; `None` retains the shared no-override convention.
- Removed the unimplemented `palette_size`, `palette_kind`, `texture`,
  `position_bias`, `anchor_corner`, and `asymmetry_force` declarations. These
  names, like other unknown keywords, now raise explicitly. This is an
  intentional version-3 interface correction. Colors come from all nine nonzero
  colors; no fixed numeric color determines an object's semantic role.
- Original random-only lessons could have three demonstrations with only codes
  {0,3}, then query codes 1/2 (seed 6, indices 38–41). The default period-2
  schedule alternates teaching and varied inputs. Three demonstrations are
  requested. Every ordinary consecutive four-input window contains two teaching
  inputs; holding one input out still leaves a teaching input in its three demos.
- The first repair (3.0.0, SHA `56ec1aabe5b42ca1e628f43dbde7f8e3d2b8b36b66f1a94a4dd52e7ad5bf1650`)
  passed its seven-rival checks, but independent review found an omitted rival:
  reverse the left tiebreak for equal-top objects. At easy seed 6, indices 0–3,
  this rival fit all demos and changed the query. Its Racket-confirmed
  counterexample and failing regression remain in `checks/tie-order-before/`
  in return `review-fcac4ea7f9b85c18`.
- Version 3.0.1 puts tall A left of singleton-height B at the same top row.
  C lies below A, extends leftward, and ends at A's leftmost column. A/B share
  exactly one row; A/C share exactly one column; B/C share neither. This makes
  both the left tiebreak and the different bottom/center order observable.
  Horizontal reflection was removed from teaching inputs because it can erase
  the simultaneous ordering contrast. Sizes, offsets and colors still vary.
- Teaching inputs with extra objects use a reserved separated bottom row.
  Varied inputs retain free bounded placement, rectangle dimensions 1–4, and a
  complete 3×3 lattice fallback. The ordinary branch has no teaching-row rule.
  Default teaching counts are 3–4; exact count 2 uses the varied construction.
- Half of default inputs draw canonical height/width/object-count profiles,
  then create new layouts. The ordinary branch retains every count 2–7 and
  dimensions across the full declared ranges in every difficulty. Profile
  support does not replay canonical grids or labels.

## Evidence and retained audit disposition

Two prior `needs_triage` findings were used as leads and reproduced against
baseline `94393710390c29870ed10b6ff8be6a8faff44087cdeff0ff2100372cf20549a3`:
`review-79c697b6421ee247:v0001` (ignored controls) and
`review-ff8ab5cf2cb86363:v0001` (untaught row/column query).
Intake explicitly resolved both findings against accepted source
`0ba5665018235581095d844bd1ad759c0ee30fb5b9d36c4602bf5c45d130fd4e`.
The 660 joint-control regression cases, 23,940-draw report and production/rotation
censuses are reviewer-reported evidence. Task-local regressions and relation
witnesses retain the useful repair evidence. No unrelated audit is closed.

Final-source evidence in return `review-fcac4ea7f9b85c18`:

- `checks/after-final/`: 12/12 battery stages green with required rotations;
  23,940 accepted exact-control draws, zero findings/warnings; 31/60 exact
  canonical profile hits (easy 8/20, medium 13/20, hard 10/20), and all five
  canonical inputs accepted.
- `checks/task-tests-final-source/`: 96 pytest tests plus 26 subtests pass
  (122 passing JUnit cases), zero failures/errors/skips.
- `checks/lesson-census-final.json`: Racket production census, 100 lessons per
  band, three demos and one query; 300 lessons, 1,200 distinct inputs and 1,200
  hold-one-pair-out rotations, with zero ambiguities/errors/hook warnings.
- `checks/schedule-census-final.json`: fixed seed 0, both declared starting
  residues in every band; 6 overlapping lessons, 24 rotations, 7 globally
  distinct inputs, zero findings.
- `checks/tie-order-after/sampler.json`: independent Python geometry probe,
  seeds 0–39, every band and both starts; 600 draws, 310 distinct inputs,
  240 windows and 960 rotations, zero failures. This is separate from Racket
  production materialization and its rejection handling.
- Eight unique rivals are checked: bottom, center, left and color ordering;
  reverse-left order for top ties; two-row and two-column overlap thresholds;
  and swapped row/column codes. Three of them fit all five labeled canonical
  pairs and are declared in `CANONICAL_SHORTCUTS`.

The focused tests use portable reviewer root/canonical helpers, an independent
coordinate-set oracle, all 660 legal joint controls, malformed inputs,
canonical labels, retained Racket witnesses, cyclic starts and query rotations.
The reusable `workspace/probe_sampler.py` discovers the actual declared rival
namespaces and reports hashes and uniqueness. `workspace/compact_evidence.py`
preserves oversized completed evidence losslessly; see its README and tests.

## Limits

Finite checks address the eight declared rivals, not every possible inductive
rule. Production counts refer to default three-demo/one-query lessons, plus a
separate three-demo/two-query reviewer solve. Arbitrary regrouping or lessons
constructed with exact overrides have no universal rotation certificate.
Two-object sorting rivals are answer-equivalent for the symmetric 2×2 matrix;
the hook rejects a surviving rival only when it changes the query answer.
There is deliberate structure in half the inputs; the varied branch supplies
broader layouts. Both official reviewer solve lanes retain unknown query scores,
and the superseded exposed solve is preserved separately. None is training-admitted.
## Current reviewer considerations

Source SHA-256: `0ba5665018235581095d844bd1ad759c0ee30fb5b9d36c4602bf5c45d130fd4e`.

# Decisions and limits

Assignment `review-fcac4ea7f9b85c18` was retained unchanged. Selected repair:
`dfa5c1702b4c`; final version 3.0.1, SHA-256
`0ba5665018235581095d844bd1ad759c0ee30fb5b9d36c4602bf5c45d130fd4e`.
The Racket authority remains `5264524f1c03`.

## D1 / R1: make the advertised exact controls truthful

The baseline accepted requested dimensions/counts but never consumed them.
For seed 0/index 0/easy, asking for 20×20 and seven distinct colors returned
11×12 and three colors, identical to the uncontrolled draw. The retained
`review-79c697b6421ee247:v0001` finding was a lead; the current baseline check
and regressions reproduce it.

Keep three precise controls: height 10–20, width 11–20, object/color count 2–7.
Their draws use the shared keyed context, and observation recovers the same
values. Strict integers reject booleans, floats, strings and out-of-range
values. `None` follows the existing omitted-override convention. The initial
three tests requiring None rejection were incorrect; they were corrected
without changing the intermediate generator. Both receipts remain.

The original rationale for advertising the other six controls is not recorded.
Implementing palette kind, texture, position bias and related names would add
new semantics without a grounded contract. They were removed explicitly, and
unknown names now error. This version-3 API correction is a compatibility
change, not a claim that those previously ignored options became functional.

The ordinary branch retries complete placements, then falls back to a
constructive separated lattice. Returning a partial count, clipping a requested
value, or declaring feasible small-grid combinations incompatible were rejected.
All 660 joint legal integer combinations are tested, along with boundary
controls in both phases and all bands. The final shared audit accepted
23,940 draws with zero findings or warnings.

## D2: retain the solid-rectangle domain and the reference rule

The canonical data has four train pairs and one labeled test pair. Every input
has distinct-color, solid, separated rectangles. Their relation matrix depends
on inclusive projection overlap in top/left order: rows contribute 1 and
columns contribute 2; the diagonal is 3. The original rectangle rationale
beyond these examples is unknown.

Two disjoint solid rectangles cannot overlap in both row and column projections:
that would imply a shared cell. Therefore off-diagonal 3 is impossible in this
domain, and its absence does not justify introducing interlocking shapes.
Repeated colors and touching objects would also change object extraction and
were rejected. Dimensions 1–4 remain supported; the prior smaller-object bias
must not exclude canonical boxes of side four. Validation now rejects
malformed grids and illegal color types without crashing.

No canonical row, Racket source, shared helper, catalog, frozen root fixture,
or audit-target source was changed. Selected canonical raw rule-text SHA-256:
`573b82b95b45ec83e1b9dd6b3d45279bcbefe2016f66922b9081d4958d9b25c3`.
The wrapped executable text has a different SHA
`e8946c22d8e3a9b1aa7336caa3f60dc163a8e02e45e3e3494f9930b84c33e274`;
these identities must not be conflated.

## D3 / R2: teach complete lessons, not only valid individual inputs

The old seed-6 medium lesson at indices 38–41 had demos containing only {0,3}
and a query introducing 1/2. A code-swapping rival could therefore agree with
all demos yet change the query. Merely adding more random examples or relying
on average witness frequency would not establish lesson coverage.

A period-2 schedule alternates teaching and varied inputs, with three demos.
Every consecutive four-input window has two teaching examples. Holding out
any one pair leaves at least one teaching example among the remaining three.
The final default teaching example refutes all eight declared rivals at once;
the Racket censuses separately check actual materialization, accepted indices
and every query position. This avoids claiming that direct draw arithmetic
alone covers production rejections.

The declared rivals are bottom-edge sort, vertical-center sort, left-first
sort, color sort, reverse-left tiebreak at equal tops, a two-row overlap
threshold, a two-column threshold, and swapped row/column codes.
The first, second and two-row threshold fit every one of the five labeled
canonical pairs. Reversing top ties fits all four canonical demonstrations
but fails their labeled test, so it belongs to lesson competitors rather than
the all-pairs canonical-shortcut declaration.

Two-object sorting alternatives sometimes survive because permutation leaves
the symmetric 2×2 output unchanged. The hook asks whether a rival both fits
the demonstrations and changes the query. Rejecting answer-equivalent rivals
would create false negatives. Explicit count-2 draws therefore remain legal.

## D4 / R3: reverse the first repair's ordering decision

The first repaired source, 3.0.0 / SHA
`56ec1aabe5b42ca1e628f43dbde7f8e3d2b8b36b66f1a94a4dd52e7ad5bf1650`,
passed its 12-stage battery and seven-rival 300-lesson/1,200-rotation census.
An independent review added a rival reversing left order only at tied top
coordinates. At easy seed 6, indices 0–2 did not refute it and query 3 differed.
Across seeds 0–39, three bands and both starts, 20/240 production windows
were ambiguous; 80/240 windows had at least one ambiguous query rotation.
Public Racket application confirmed the four saved counterexample labels.
The added regression failed on 3.0.0.

The final layout puts a four-row A on the left and a one-row B on the right
with equal top coordinates. C sits below, extends leftward, and ends exactly
at A's leftmost column. A/B overlap in one row; A/C in one column; B/C in
neither. This simultaneously makes the left tiebreak, bottom/center ordering,
and one-cell thresholds observable.

Horizontal reflection was removed from the teaching branch because it can
remove the bottom/center contrast after tying the tops. Keeping reflection
merely for apparent variety was rejected. Widths, heights of C, offsets and
colors vary; the separate ordinary branch remains free to place rectangles.
The eighth rival, minimal witness, failing test and original candidate source
are retained. Passing old reports are clearly intermediate.

## D5 / R4: restore canonical support without replaying examples

Even-index teaching draws select one of the five canonical
(height,width,object-count) profiles:
(12,14,3), (11,13,4), (10,12,3), (13,15,4), (12,13,4).
The profile auditor counts palette size including background, so its third
coordinate is one larger. Layouts and colors are drawn anew.

Odd-index varied draws cover heights 10–20, widths 11–20 and all counts 2–7.
Difficulty weights favor smaller counts for easy and larger counts for hard,
but do not remove any count. Uniformly growing every grid or replaying exact
canonical grids would respectively miss the profile floor or reduce useful
variation. Half-profile sampling supplies predictable teaching support and
still permits a broad alternate branch.

The final shared profile floor sees 31 exact hits in 60 draws:
easy 8/20, medium 13/20, hard 10/20; it accepts all five canonical inputs.
The first repair's 32/60 result applies only to its own source.

## D6: choose constructive capacity and disclose its restriction

Teaching draws with four through seven objects reserve a separated final row
for the additional singleton rectangles. This guarantees exact capacity even
at 10×11 with seven colors. A dense rejection-only teaching layout could
silently fail to honor legal controls, so it was rejected. This last-row
restriction belongs only to teaching inputs.

Colors are selected without replacement from 1–9. Teaching inputs are recolored
until numeric-color sorting disagrees, with a constructive fallback. This
does condition palette order in that branch, which is disclosed; there is no
fixed object/color mapping. The ordinary branch is not conditioned this way.
Tests establish the stated geometry/competitor properties, not statistical
independence or absence of every undeclared shortcut.

## D7: validation scope and reproducibility

Final source-bound checks:

| Check | Population | Result |
| --- | --- | --- |
| Required-rotation battery | Standard 12 stages | 12 green, no advisory/failed/incomplete stage |
| Exact controls | 23,940 shared audit draws | All accepted; zero findings/warnings |
| Portable focused tests | 96 tests + 26 subtests | 122 JUnit cases pass, zero failure/error/skip |
| Racket lesson census | 100 lessons per band; three demos, one query | 300 lessons, 1,200 distinct inputs; production and 1,200 rotations clear |
| Fixed-seed schedule census | Seed 0; both period-2 starts × all bands | 6 overlapping lessons, 24 rotations, 7 distinct inputs; clear |
| Independent geometry probe | Seeds 0–39; both starts × all bands | 600 draws, 310 distinct inputs; 240 windows/960 rotations clear |

The larger census seed formula and all accepted indices/instances are saved
in `checks/lesson-census-final.json`. Rotation means holding out each pair once
while retaining the order of the other three. Fixed-seed coverage is complete
only at that seed; the larger finite sample is broader, not exhaustive.
Explicit-override lesson assembly, arbitrary external regrouping and
undeclared hypotheses remain outside the demonstrated guarantee.

Official portable tests initially failed at dependency preflight with zero
tests executed. A virtual environment with numpy, Pillow and pytest was
prepared and used for both wrapper and payload, preserving the deliberate
user-site isolation. No shared isolation rule was relaxed. The exact final source patch was checked/applied to a fresh original extraction,
and that copy passed 96 tests plus 26 subtests in its own portable runtime.
The replay receipt originally assumed one generator binding, but the normal
runtime has both an import copy and a task snapshot. Both hashes match.
The failed receipt assertion and original script are preserved; the corrected
receipt finalizer checks every binding and every changed-file hash without
rerunning or relabeling the passing tests. See `checks/fresh-replay/` and RESULTS.

## D8: solves, audits and retention

The blind task a452b4b4f04a was solved before repair material was opened.
The later solve is honestly exposed. A first exposed solve bound to source
3.0.0 was archived before preparing and completing the 3.0.1 solve from its
visible examples. Every submitted revision and finish note remains; each
episode passes 3/3 visible examples on its first attempt, with query scores
unknown. A source-mismatch prepare failure and a pre-attempt capacity failure
are infrastructure records, not invented wrong model solutions.

Audits were drawn once and remained findings-only. dded62bb9e3a has a
reproduced ignored blob_size control, plus separately scoped existing shortcut
and domain observations. The bounded 2acfd448f58b audit found no issue.
The latter verifier's first failure incorrectly equated raw and wrapped
Racket source hashes; both versions and corrected verification are preserved.

The oversized original before-override report is losslessly compressed with
a portable size/path/SHA manifest, a verified retained original, and a tested
restore command. No failure records were dropped. Shared tooling was left
unchanged; the task-local utility is reusable and F1 proposes shared adoption.
