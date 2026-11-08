# 1ee7274bdbb0 — current generator decisions

## Current native extension — review-0ef1d91dd4d9916e

`workspace/parametric/` now supplies a self-contained native adapter with
`turn=cw|ccw` and `post=none|settle_down`. `cw/none` returns the exact selected
canonical program, SHA-256
`a23915e769b96d7ca844d36d4b8408b311d672bca58166fad83378fa83cf8660`.
The production generator remains version 5.0.0, SHA-256
`361b58f0b05755fb012c1cea746d6b0add06cb4a1573a353466df2e566e4ce72`, with its
existing rule pin and approval identity.

The post-operation moves the entire transformed motif downward by one common
displacement, preserving disconnected components, holes and relative offsets.
Step A's marker-selected whole-tile quarter-turn produces the occupied-cell set
whose lowest row determines step B's displacement. The protected wrong-order
witness swaps settling and turning in the exact qualified programs. Two replayed
cases differ by 36 cells (clockwise) and 16 cells (counterclockwise). This is a
geometric state dependency, not iterative simulation or a training-gain claim.

Constructive episodes support independently 2–6 demos and 1–4 queries, default
to 3/4, and build the full bank before slicing with matched inputs across all
four settings. Two core scenes combine marker counts 0/1/2/3, direction/pivot
witnesses and varied motif topology within each scene. They distinguish the
declared rivals even after the chosen post-operation; settling can erase a raw
rotation difference, so raw-shape distinctions alone were not treated as proof.
These cores replace the need for the production six-demo schedule in this
separate assembly. The production schedule's own contract remains unchanged.

The native grammar uses exact integer colors `{0,2,3,9}`, single full dividers,
uniform square tiles and axes 3–30. A single square tile is an explicit extension.
A regular multi-tile axis has length `n*(s+1)-1`; exact 30 requires `n*(s+1)=31`
and therefore one 30×30 tile. The bank also includes nine 9×9 tiles in a 29×29
lattice. Dense 30×30 cases have over 300 motif cells across all quadrants and
positive settling distance in either turn direction. Markers touch canvas edges.
Other profiles reach 3×3, 19×19 and 27×27 with substantive geometry.

Current evidence in `checks/1ee7274bdbb0/`: **78 focused native/audit tests**;
**192/192** sampler/count/prefix requests across 16 seeds; **200 rival/episode
comparisons all refuted by the first two demos** using 258 distinct protected
Racket evaluations, including all 80 bank labels. A preliminary literal-fixture
check separately compared 264 rival evaluations with independent Python.
Native qualification passed eight jobs at six demos/four queries with 224
protected evaluations. Both causal cases replayed, and eight private episodes
produced 32 verified one-query public files. `checks/first-turn/report.json`
checks all 48 views across both builds and all 12 first turns under six private
or future-query mutations plus visible-cell positive controls. The source-bound
inventory is `workspace/parametric/evidence/manifest.json`.

A fresh static review requested no source changes. Evidence is finite in seeds,
profiles and declared rivals; it does not establish universal identification.
Initial expected missing-implementation test failures are retained. Production
batteries were not rerun. The current production audit
`review-3ac21549f2aae7f7:v0001` remains **needs_triage**: invalid difficulty and
coercible typed production controls are accepted. Strict native controls do not
resolve that separate production API finding or change its disposition. Next
owner action is native qualification and fresh acceptance of both exact integrated
sources; reviewer readiness grants no training admission or activation.

## Rule and domain

VERSION 5.0.0 retains canonical Racket RULE_HASH `a23915e769b9` unchanged.
Full color-9 dividers form square tiles. Recolor every 2 to 8; rotate a motif
clockwise around its whole tile iff any 3 is present; remove the 3s. Legal
controls remain tile_size 3..5, n_tile_rows 1..3, n_tile_cols 2..4,
anchor shape_size 1..6, anchor rotate_flag boolean, common n_flag_cells 1..3.
Every input has both marker branches, changing motifs, and at least two sizes.
Unknown keys raise. Exact controls take precedence over difficulty and schedule.

## Seven-phase teaching schedule

Default marker counts repeat `(1,1,1,2,2,3,3)`. `EXAMPLES_NEEDED=6`: six
demonstrations plus one query contain all seven consecutive phases.
Phase 0 permits centered markers, alternating flags, all lawful motif
topologies and symmetries. Phases 1 and 2 retain canonical 3x11 geometry but
guarantee an off-center single-marker witness. Phases 3..6 provide two
double-marker and two triple-marker examples, strong direction witnesses,
and the medium/hard extension sizes. Phases 1..6 refute alternating tile
selection when at least three tiles exist.

This duplicates evidence against the 16 named rivals, including seven that
fit all three labeled canonical pairs. In any default seven-consecutive-pair
window, a witness remains when any one pair becomes the query. Explicit
controls, shorter lessons, arbitrary nonconsecutive assembly, or multiple
simultaneous held-out pairs do not inherit that structural guarantee. The
lesson hook still checks its actual supplied demos and each query. This is
a finite rival contract, not universal identifiability or training admission.

## Repairs and reversed decisions

The July associated notes for return `review_response_external-local-random_87ad3fe1f3af_x`
were used as historical leads only; the referenced old check files were not
available here and were not counted as fresh evidence. No review_index.json
or audit-dispositions file was present for this target.

- Prior hard-only large geometry left hard canonical support at 0/20. Now
  three of seven phases preserve strict canonical structure in every band.
- The first two tile sizes, flags and topology are no longer fixed unequal,
  opposite, or connected/disconnected. Repair only all-equal size/flag cases;
  keep the top-left exact controls. Phase 0 admits all three canonical inputs
  structurally, including equal first-two counts and symmetric motifs.
- Connected masks now grow through a sorted frontier and have an exhaustive
  finite fallback. This fixes ordinary seed 0/index 41096 and exact-control
  seed 0/index 1543; connected-shape frequencies change, while feasible
  connected shapes retain support. Markers reserve both an outside-answer
  cell and an uncovered answer cell, repairing the singleton/two-marker case.
- A first repair with five demonstrations missed the single-marker/center
  hybrid. The retained Racket-labeled counterexample motivated the final
  seven-phase, six-demonstration schedule; the failed iteration is preserved.
- Task tests now locate canonical data with reviewer_support.find_root and
  canonical_pairs and load the selected generator in either portable layout.

## Evidence and reusable checks

Return `review-5339bc49ee268b8b` retains before/intermediate/final receipts.
Final source SHA-256: `361b58f0b05755fb012c1cea746d6b0add06cb4a1573a353466df2e566e4ce72`.
The after battery passes all 12 stages with zero advisories. Exact controls:
16,650/16,650 accepted draws, no findings or warnings. Focused and portable
task runs: 148 tests each, zero failures. The source-bound production census
has 100 lessons per band, 2,100 distinct inputs, and zero ambiguity/errors in
300 lessons and 2,100 single-query rotations (`checks/lesson-census.json`).
The separate schedule census checks seed 0, all starts 0–6 in all bands:
21 overlapping lessons, 147 rotations and 27 unique inputs, with no ambiguity
or execution errors (`checks/schedule-census.json`).

`workspace/reviewer_rival_probe.py` independently extracts tiles, dynamically
reads the current rival declarations, and verifies sampled labels with real
Racket. Its final bounded probe verified 52/52 labels; its 48 generated draws
have 31 distinct inputs because canonical phases can repeat across bands.
See `counterexamples/reviewer_marker_shortcuts.json` and
`counterexamples/reviewer_sampler_failures.json` for exact cases. No Racket
authority, approval ledger, shared runtime, or audit target was edited.
## Current reviewer considerations

Source SHA-256: `361b58f0b05755fb012c1cea746d6b0add06cb4a1573a353466df2e566e4ce72`.

# Decisions — 1ee7274bdbb0

Source: VERSION 5.0.0, SHA-256 `361b58f0b05755fb012c1cea746d6b0add06cb4a1573a353466df2e566e4ce72`.
Canonical Racket rule `a23915e769b9` is unchanged. The assigned repair changes
sampling, semantic contracts, tests, current notes and task-local reproducers.

| Choice | Prior rationale / defect | Selected repair and evidence | Alternatives and limits |
|---|---|---|---|
| Canonical scale in all bands (`R3-PROFILE`) | July associated notes intentionally relied on easy to supply the pooled floor. Current hard baseline had 0/20 exact-profile hits. | Three of seven phases retain canonical 3 × 11 geometry and single markers; after hits easy 20/20, medium 9/20, hard 9/20. Semantic strict rate 271/600 exceeds unchanged 0.30 floor. | Keeping hard-only large shapes fails the current per-band requirement; making every draw canonical would lose larger-lattice variation. |
| Whole lessons teach marker roles (`R4-SHORTCUTS`) | Baseline checking eight transforms omitted canonical-fitting marker-count and positional rules. Two public production episodes were genuinely ambiguous. | Seven phases `(1,1,1,2,2,3,3)`, six demos+one query, with duplicated off-center/count witnesses and 16 explicit rivals. 300 real lessons and 2,100 rotations found no ambiguity. | Random marker counts can leave the query's count absent from demos. Five demos were tried and failed on the single-marker/center hybrid; that intermediate is retained. |
| Canonical structural support (`R5-SUPPORT`) | Forced first-connected/second-disconnected motifs, distinct first-two sizes and per-tile reflection distinctions excluded canonical patterns. | Independent size/topology placement; repair only globally equal counts; allow symmetric-but-rotating motifs in core phases. Phase 0 permits every actual canonical motif, flag and marker layout. | This is source-level support, not a claim that a searched seed reproduced each whole canonical grid. Strong transform witnesses remain in four extension phases. |
| Position is not the flag | Forcing the first two flags opposite allowed an alternating-position rival to fit canonical data and complete generated lessons. | Sample mixed flag layouts; noncanonical teaching phases forbid the alternating rival when there are at least 3 tiles. Phase 0 still admits the canonical alternating patterns. | A two-tile exact override with both branches is necessarily alternating; that control remains legal and has a narrower lesson guarantee. |
| Total legal mask sampling (`R1-SAMPLER`) | Uniform subset rejection occasionally exhausted 1,024 attempts for sparse connected 5 × 5 motifs, including an ordinary unoverridden draw. | Connected frontier growth plus finite exhaustive fallback; marker feasibility is included in the acceptance predicate. Retained regression seeds now pass. | Relative connected-shape probabilities change; support is retained. The fallback can examine 177,100 subsets in a pathological case. Raising the retry cap alone would retain the failure mode. |
| Marker versus answer witness (`R2-MARKERS`) | The old placement guaranteed a marker outside the answer but could cover an entire singleton answer with additional markers. | Reserve an uncovered rotated-answer cell when needed, plus an outside-answer marker. Honor exact counts and center exclusions; dense 3 × 3 six-cell/three-marker cases remain feasible. | Do not reserve an unnecessary extra empty cell if a motif/forbidden cell already protects an answer cell. |
| Controls and tests (`R6-CONTROLS`, `R7-PORTABILITY`) | Unknown keys were silently swallowed; canonical tests used a fixed parent-depth path and failed portable preflight. | Reject unknown keys; keep all six integer/bool controls and their bounds. Use portable root/data helpers and explicit selected-source loading. 16,650 override draws and 148 portable tests passed. | No float/string coercion contract change was introduced. User-site pytest is deliberately unavailable in the portable runtime; use a venv with pytest installed. |
| Shared tooling (`F1`) | Baseline had 10 green + 2 advisory stages but its footer said all 12 green. | Optional tested patch under `checks/tooling-advisories/` fixes reporting and cached-failure status. | Protected shared sources remain unchanged; accepting this optional patch is a separate maintainer choice. |

## Scope of the teaching evidence

The guaranteed assembly is seven consecutive default accepted pairs: six demos
and one query, or any single-query rotation of those seven. The public census
used 100 lessons per band and Racket labels, with 2,100 unique inputs and 2,100
rotations. Focused tests exercised every cyclic start for three explicit seed
families. Named-rival checks are finite; new composite hypotheses can remain.
Explicit overrides, fewer demos, nonconsecutive assembly, and multiple held-out
pairs require their own checks. The post-repair solve uses six demos and two
queries; its actual supplied lesson hook passed, but this does not extend the
structural guarantee to arbitrary two-query rearrangements.

A separate public census enumerated seed 0, requested starts 0–6 in all
three bands: 21 overlapping lessons, 147 pair appearances, 27 unique inputs
and 147 query rotations, with no ambiguity or execution errors. The coverage
claim uses `schedule_coverage.period=7` and actual lesson indices in
`checks/schedule-census.json`; its legacy `sampler.period=6` field is a
residue-summary parameter, not the declared schedule period.

## Evidence and reversals

Historical lead: `evidence/associated_notes.jsonl` references the July return
`review_response_external-local-random_87ad3fe1f3af_x`. Its old external logs were
unavailable and were not reused as measurements. There was no review index or
audit-dispositions file for the selected task. Baseline, helper-only and
intermediate-five-demo sources/results are separately pinned under `checks/`.
Minimal original sampler failures and final marker counterexamples are retained
in the selected task's `counterexamples/`; `workspace/reviewer_rival_probe.py`
rechecks current declarations and real Racket outputs for future reviewers.

## Self-review

The repair preserves a phase with the canonical marker, topology and symmetry
patterns, while retaining broader size/control support and removing fixed
positions that could stand in for markers. Its stronger lesson contract costs
three additional demonstrations relative to the original default and remains
limited to the declared rivals and specified assembly; it does not confer
training admission or change any audit target.
