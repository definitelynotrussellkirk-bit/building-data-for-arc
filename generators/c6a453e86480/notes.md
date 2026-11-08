# Current notes: c6a453e86480, version 2.0.0

## Rule and support

The unchanged canonical Racket authority (`RULE_HASH = 1971dd8a407b`) reads
nonzero top-row colors from left to right, finds four-connected color-1 body
components, sorts by minimum column over every cell, and recolors by that rank.
Production labels always come from Racket. Python predictions are diagnostic
rivals and are checked against actual reference outputs.

The sampler supports 3 or 4 distinct legend colors in 2..9 with equally many
body components. Background 0 and body color 1 are fixed roles. Row 1 is blank;
row 2 is usable. Components have distinct minimum columns and do not touch
orthogonally. The validator handles malformed arrays and rejects foreign body
colors. It allows lawful larger canvases within ARC's 30-cell bound, while the
advertised sampler controls are `grid_h=5..10`, `grid_w=10..16`, and `n_blobs=3..4`.

`palette_kind` and `texture` are aliases with the same four observable categories.
Warm uses only {2,4,6,9}; cool uses only {3,5,7,8}; default includes both 2 and 3;
varied is a mixed warm/cool set without both 2 and 3. Colors within the legend
are shuffled. Unknown keys, non-integer integer controls, and conflicting aliases
raise explicitly. The former ignored `palette_size`, `n_distinct_colors`,
`position_bias`, and `density` controls were removed; invalid diagnostic textures
now raise rather than return unusable grids.

## Decisions and reversals

- Fixed-three prior choice -> exact three/four support: canonical train[1] has
  four components. The original validator rejected it and could not generate
  its six-color profile.
- Occupied rows 0 and 1 -> reserve row 0 only for random growth: the shared
  helper excludes occupied cells' neighbours, so the old reservation also
  excluded row 2. All three canonical inputs use row 2.
- Unstructured random placement -> alternating focused even indices and random
  ordinary odd indices. The ordinary fallback constructs a lawful focused shape
  without shrinking requested counts or dimensions.
- Intermediate two-row hook -> middle-row left arm with right tips above and
  below: the first repaired source still admitted a bottom-row-order ambiguity
  at seed 12, indices 8..11. Actual Racket labels confirmed the rival fit all
  three demos and changed the query. `counterexamples/rank_ordering.json` is the
  final default-production witness; the full intermediate source and lesson
  remain in the return's `checks/intermediate-*` evidence.
- Legend alignment is permitted accidentally. The requirement is independence
  from alignment, not a categorical ban on matching columns.

## Teaching contract and limits

There are 10 rivals that fit all 3 canonical labeled pairs: row-major,
centroid, rightmost, bounding-box center, descending area/bounding-box area/width,
first occupied pixel's column, bottom-row column, and cellwise vertical bands.
Numeric legend ordering is an additional competitor, already refuted canonically.
Every default focused input refutes all 11. Four numerically consecutive,
unskipped sample indices contain two focused inputs; after any one pair becomes
the query, a refuting example remains among the three demonstrations. A
three-example prefix of unskipped indices contains a focused input. Duplicate
rejection may skip indices, so parity alone does not prove this invariant for
all accepted production windows.

The actual production census used 3 demos and 1 query, 100 hash-seeded lessons
per easy/medium/hard band, requested starts 0..99, and every single-pair holdout.
Production uses the first three accepted draws as demos and the fourth as query.
It found no ambiguity in 300 lessons / 1,200 rotations against these 11 distinct
rivals (the census retains 32 namespaced declarations), with 1,200 unique inputs.
This is finite evidence, not universal identification. Duplicate rejection can
advance indices; use the actual accepted-index metadata, not requested starts,
when extending the argument to another sampler.

Explicit `grid_h=5` remains a lawful input override and refutes the original
10 competitors, but its smaller hook does not refute bottom-row ordering. The
all-11 witness guarantee applies to default focused inputs; production lesson
results are the finite census above. Height-fixed override lessons need their
own checks. Default focused cases use height 6; ordinary draws
retain the five-row canonical profiles. Focused shapes are deliberately more
structured than ordinary shapes; untested shape-conditional rivals remain possible.

## Verification and current status

Final generator SHA-256: `6a95f82e3d6d87916a4bd854061742a4232f8bb704055f68fb0f4224d4885e31`.
Final battery: 12/12 stages green, strict input check 600/600, canonical inputs
3/3 accepted, and exact-profile hits easy 16/20, medium 14/20, hard 9/20.
Portable task tests: 52 cases from 12 test functions, 0 failures/errors/skips.
The task probe passed 2,016 full joint-axis cases and 16 actual Racket cases,
including a palette permutation fixing 0/1 and the former ambiguous seed window.
The independent geometry review checked all 24,696 constructive parameter tuples;
height-5 and height-6..10 claims were scored separately.

There was no inherited review_index.json, associated note, or task test in this
selected baseline; no prior return was used as a lead. No unresolved selected-task
finding remains from this review. See `tests/test_rank_distribution.py`,
`workspace/probe_rank_distribution.py`, and the return's `RESULTS.json` for replay.
## Current reviewer considerations

Source SHA-256: `6a95f82e3d6d87916a4bd854061742a4232f8bb704055f68fb0f4224d4885e31`.

# Decisions for c6a453e86480

Final source: 6a95f82e3d6d87916a4bd854061742a4232f8bb704055f68fb0f4224d4885e31. Canonical Racket source and labels were not changed.
The selected baseline had no retained task notes, tests or review index; the
original author rationales below are unknown except where code comments explain them.

## Domain and controls

1. **Three and four objects.** Prior code fixed three objects, probably reflecting
   the first canonical pair (rationale unknown). The second canonical training
   pair requires four. Support exactly the two demonstrated counts for this
   repair; broader 1..8-object support remains a separate distribution choice.
2. **One separator.** Reserve row 0 for grow_blob, whose adjacency rule excludes
   row 1. Reserving rows 0 and 1 also excluded row 2; the regression demonstrates
   that source-level mismatch and the final probe measures row-2 reachability.
3. **Real controls.** Preserve exact dimensions across every difficulty band,
   choose the requested blob count, implement observable palette categories,
   and make texture a checked alias. Retire four ignored singleton controls and
   invalid-grid textures. Keeping inert compatibility knobs would continue to
   mislead callers; explicit rejection makes migration visible.
4. **Palette roles.** Keep 0 background and 1 body fixed; legend colors 2..9 are
   task-defined by their ordered positions. Warm/cool/default/varied sets are
   disjoint observable classes. Numeric legend sorting is suppressed in focused
   cases but remains possible in ordinary samples. The color-role permutation
   fixes 0 and 1 and was checked with the actual Racket reference.
5. **Grid profiles.** Ordinary cases retain all three canonical height/width/count
   anchors. Every fourth index has broader dimension support, with difficulty
   increasing the height cap; overrides always use the full advertised bounds.
   Default focused cases require at least six rows after the bottom-row repair.
   Final pinned 20-draw exact-profile counts are 16, 14 and 9 for easy/medium/hard;
   none opts out of the floor. Larger dimensions alone are not a claim of deeper
   reasoning difficulty.

## Teaching schedule and rejected alternatives

The rank is the minimum column of the entire component. Row-major discovery,
centroid, rightmost column, bbox center, area, bbox area, width, first-pixel column,
bottom-row column and cellwise vertical bands all fit the 3 canonical labeled
pairs. The last alternative avoids object recognition entirely. These ten
hypotheses are declared in CANONICAL_SHORTCUTS and dynamically scored by the
reusable probe. Numeric legend order is the eleventh competitor; it does not fit
all canonical labels and is therefore not advertised as a canonical shortcut.

Unstructured random growth alone offers no per-lesson teaching guarantee.
Default even indices therefore use a constructive witness and odd indices keep
random shapes. The reference-visible evidence distinguishes all eleven rivals
on every focused default. With 3 demos + 1 query from four numerically consecutive, unskipped
sample indices, two focused examples exist and any one query holdout leaves at
least one. A three-demo prefix of unskipped indices contains an even index.
Duplicate rejection can skip indices, so this parity argument alone does not
prove the same invariant for all accepted production windows.

The intermediate design used a bottom horizontal bar and passed every standard
stage against its then-declared rivals. Independent review proposed bottom-row
column rank. Actual Racket output confirmed an ambiguity at seed 12, indices
8..11; checks/intermediate-bottom-row-ambiguity.json preserves it. Merely adding
a warning was rejected because the defect was concrete and repairable. The
final shape puts its minimum column in the middle row, with a right tip above
and below, refuting both first-pixel and bottom-row proxies. The height-5 exact
override keeps the older legal shape because the chosen joint witness needs
another row; height-fixed lessons must be checked separately.

The 300-lesson census used the production sampler, 100 seeds per band, requested
starts 0..99, with the first three accepted draws used as demonstrations and
the fourth as production query; each of the four labeled pairs was also held
out once. Results: 300 materialized lessons, 1,200 labeled pairs / unique inputs,
0 ambiguities, 0 warnings/errors, and 0 ambiguities in 1,200 rotations. The seed
recipe and actual accepted sample indices are retained. Rotations reuse examples
and do not enumerate every possible cyclic lesson or prove universal induction.
Local tests also cover four consecutive starts spanning both focus parities.

## Reusable tools and geometry evidence

workspace/probe_rank_distribution.py uses public canonical helpers and
Catalog.apply. It reads the live rival declarations, tests 2,016 complete
joint-axis combinations at both parities (seed 20261007), samples 120 default
inputs per band using seeds 20261007..20261016 / indices 0..11, and checks
16 actual Racket cases. Its output records replay settings and every failed case;
it returned zero failures. Each band's 120 default grids was distinct within
that band; these counts are not asserted to be globally distinct across bands.

The independent exhaustive construction review retained its exact executable
probe and captured output: 686 height-5 configurations refute the original ten
competitors; 24,010 height-6..10 configurations refute all eleven. Geometry was
checked with an independent component census, while its color legend was fixed
and nonascending. This is finite constructor coverage, not all arbitrary grids.

## Remaining limits and handoff choices

The fixed role colors, three/four count domain, unique component minima and
blank separator are intentional current restrictions. Stronger shape-conditional
or compositional rivals were not exhaustively searched. Production rejection
can skip indices, so actual lesson evidence—not requested starts alone—must be
used if the sampler changes. No inference trajectory or query answer is admitted
to training by this repair.

Both audit targets were left unchanged. Audit results are findings-only and are
retained with their own hashes. The original failed battery, failed portable
prerequisite attempt, intermediate semantic miss, and corrected audit comparator
failure remain available; a later green result does not erase them.
