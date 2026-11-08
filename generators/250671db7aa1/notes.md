# Current notes: 250671db7aa1

## Intended rule and authority

A complete row or column of color 5 is a reflection axis. Preserve the input and
copy every nonzero, non-5 cell to its exact mirror coordinate across that painted
axis, preserving color. The canonical Racket authority was not changed.
`RULE_HASH` is pinned to `27bdc557ee50`.

## Reproduced baseline defect

The inherited v1.1.1 distribution generated only a centered vertical axis and a
single monochrome blob on its left. Its validator only checked for a color-5
column and accepted missing/no-op/ambiguous scenes. Several advertised controls
were dead, aliased, singleton, or deliberately degenerate; the source did not pin
the authority hash or expose a lesson-identifiability contract.

That distribution allowed at least four rules to fit every canonical pair:
reflect only from the lower-coordinate side, reflect only the modal color,
reflect only the largest source component, and reflect across the geometric
center. The first is the strongest directional shortcut because every canonical
source is left of a vertical axis or above a horizontal axis.

## Current decisions — version 3.0.0

1. Preserve the Racket rule and broaden only the generated input distribution.
2. Replace descriptive/dead axes with eight exact observable controls:
   `grid_h`, `grid_w`, `orientation`, `axis_bias`, `source_side`,
   `source_cells`, `n_distinct_colors`, and `pattern`.
3. Use a four-slot cyclic curriculum covering both orientations, both source
   directions, centered and off-center axes, one and multiple colors, and compact
   and disconnected sources. A lesson contains four demonstrations plus one
   query; every possible single-pair holdout retains a contrast for every named
   rival.
4. Require source cells to occupy one side only, reflect in bounds onto blank
   destinations, and use at least two reflection offsets. Reject missing axes,
   multiple axes, stray color-5 cells, no-op scenes, two-sided sources,
   collisions, malformed cell types, unknown overrides, and inexact integer
   controls.
5. Keep seven executable lesson competitors. Four are canonical-fitting
   shortcuts; the orientation-only and opposite-side variants protect the
   complete scheduled lesson.
6. Retain an exact after-axis counterexample in
   `counterexamples/after_side.json`; its canonical Racket output is recorded in
   `checks/counterexample-250671db7aa1/racket.json` in the review return.

## Verification and limits

Final generator SHA-256 is
`b35b37b2cd0d12dc204c06dc40b490f1b1f329af2700b7141b488021f48a4cae`.
The full required-rotation battery is 12/12 green and 19 portable focused tests
pass. A source-bound random census materialized 300 lessons / 1,500 pairs and
found zero ambiguity in production or in all 1,500 query rotations. Exhaustive
fixed-seed schedule enumeration checked all four starts across three difficulty
bands: 12 lessons / 60 rotations, again with zero findings.

The finite rival set and sampled census do not prove unique induction against
all possible programs. Generated scenes intentionally keep all source cells on
one side so outputs are additions rather than conflict-resolution cases. The
validator accepts canonical-compatible dimensions up to 30 while exact generated
controls stay at 7..14. Explicit overrides can alter one scheduled property, but
the ordinary four-slot default curriculum is what carries the holdout guarantee.
## Current reviewer considerations

Source SHA-256: `b35b37b2cd0d12dc204c06dc40b490f1b1f329af2700b7141b488021f48a4cae`.

# Decisions — 250671db7aa1

## D1 — Keep the canonical Racket rule unchanged

**Inherited choice:** the task authority reflects every nonzero, non-5 cell
across a complete row or column of color 5. The inherited generator described
only a vertical case, but the canonical examples include both orientations.

**Decision:** pin `RULE_HASH=27bdc557ee50` and repair only the Python generator,
validator, tests, and lesson contract. Canonical exact parity and rule smoke show
no authority defect.

**Alternative rejected:** narrowing the Racket rule to the inherited vertical,
left-source grammar. That would encode a generator shortcut as the task law and
contradict a canonical horizontal example.

## D2 — Replace dead descriptive axes with exact task-linked controls

**Baseline:** `palette_kind`, `palette_size`, `position_bias`, `density`, and
`texture` were dead, fixed, aliased, or degenerate. `n_distinct_colors` was a
singleton and the blob controls did not expose orientation, side, or axis
location. The before lint/defect evidence is retained under `checks/before/`.

**Decision:** expose only eight recoverable properties: grid height/width,
orientation, axis bias, source side, source-cell count, distinct-color count,
and compact/split pattern. Every axis has exact observation logic and boundary
coverage in the focused tests and official override stage.

**Alternatives rejected:** retain decorative controls for compatibility, or
make every property random but not externally controllable. Both preserve an
API that overstates what can be measured and make failures harder to reproduce.

## D3 — Teach both orientations and both source directions by schedule

**Measured shortcut:** all three canonical pairs fit “reflect only from the
lower-coordinate side”—left of a vertical axis or above a horizontal axis. The
inherited generator strengthened that rival by generating only left-of-vertical
sources.

**Decision:** use a four-slot cyclic schedule:

1. vertical / before / centered / compact / monochrome;
2. horizontal / before / off-center / split / monochrome;
3. vertical / after / off-center / compact / multicolor;
4. horizontal / after / off-center / split / multicolor.

A materialized lesson contains five consecutive pairs: four demonstrations and
one query. Because any five consecutive indices contain the full four-slot
cycle plus one repeat, removing any query leaves the directional and orientation
contrasts in the demonstrations.

**Alternatives rejected:** independent random draws (unlucky lessons can omit a
branch), simply doubling `EXAMPLES_NEEDED` without scheduling (frequency is not
a guarantee), or teaching only one source side and assuming reflection symmetry.

## D4 — Add shape, color, and position contrasts that break other shortcuts

**Canonical-fitting rivals:** reflect only the modal source color, reflect only
the largest source component, and reflect across the geometric grid center also
fit all canonical examples.

**Decision:** multicolor scenes deliberately make one color frequent while
retaining minority colors; split scenes contain multiple disconnected source
components; off-center axes separate the painted line from the grid midpoint;
and every scene uses at least two distances from the axis. These properties are
observable and named by semantic witnesses.

**Alternatives rejected:** balanced color counts only (permits arbitrary tie
rules), a single disconnected point as token clutter (does not establish that
all components reflect), or keeping every axis centered (does not teach that the
painted line, not geometry, controls reflection).

## D5 — Strengthen validation at the task boundary

**Baseline:** `self_check` was acceptance-only. It allowed missing blobs,
missing or malformed axes, degenerates, and scenes whose intended behavior was
not established.

**Decision:** the shared analyzer now requires exactly one full color-5 row or
column, no stray fives, at least one source, one source side, in-bounds blank
mirror destinations, legal ARC cell types, and a realizable axis bias. Generated
compact/split scenes also use multiple reflection offsets. Unknown controls and
non-integer integer controls fail loudly.

**Limit:** the validator intentionally rejects already-symmetric/two-sided inputs
rather than defining overwrite/conflict semantics not needed by the canonical
curriculum.

## D6 — Use executable rivals and a rotation-safe lesson hook

**Decision:** declare seven pure competitors: before-only, after-only,
vertical-only, horizontal-only, modal-color-only, largest-component-only, and
geometric-center reflection. `lesson_identifiable` verifies every demonstration
against the local mirror, then rejects any competitor that fits all demos but
changes the query answer.

**Verification:** the official required-rotation battery is 12/12 green. The
large census checked 300 lessons, 1,500 pairs, and all 1,500 query rotations with
zero ambiguity. Fixed-seed period enumeration checked 12 lessons and 60/60
rotations. These checks are finite over named rivals, not a proof over all
programs.

## D7 — Follow red/green TDD and retain a minimal counterexample

The first portable focused run was intentionally red: **19/19 tests failed**
against v1.1.1 for missing metadata, controls, validation, rivals, oracle support,
and the exact counterexample. After the implementation, the same isolated stage
passed **19/19**. Evidence is retained in `checks/task-tests-red/` and
`checks/task-tests-green-1/`.

The exact right-side input in `counterexamples/after_side.json` is small enough
to inspect manually. The supported Racket authority output is retained under
`checks/counterexample-250671db7aa1/`; it differs from the lower-coordinate-only
shortcut while remaining lawful under the repaired validator.

## D8 — Keep audit findings separate from this repair

The drawn audit targets were `12a886996b14` and `0f25172eefa4`. I reproduced a
missing-red degenerate contract failure for the first and found no new issue in
the completed checks for the second. Their source files were not modified; exact
evidence and scope are in `AUDIT.md` and `checks/audit/`.

## D9 — Replay the packaged patch from its actual packet root

The first version of `checks/tooling/replay_return.py` initialized Git at the
outer extraction root, while the generated patch addresses `repo/...` paths
relative to the packet's `WORK/` directory. Its first `git apply --check` failed
before touching source. I retained that failure, added a unit test that was red
because no packet-aware root selector existed, then implemented
`patch_root(extraction_root) -> extraction_root / "WORK"` and observed the test
green.

The corrected helper applied the exact draft `patches/source.patch` to pristine
packet bytes, reproduced the selected generator SHA-256, and passed all 19
focused tests. This helper is evidence/tooling only and is not part of the
allowed repository source delta.
