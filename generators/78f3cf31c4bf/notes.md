# Working notes: 78f3cf31c4bf

## Baseline diagnosis

The selected `2.0.2` generator produced only separated L-trominoes with distinct
colors. It omitted `RULE_HASH`, advertised dead or singleton axes, exposed three
degenerate textures as ordinary values, swallowed unknown overrides, and had no
executable semantic contract or task-local tests. Although ordinary draws matched
the Racket rule, the curriculum could not distinguish several rules that fit all
four canonical pairs.

The initial full battery retained at `checks/before/` had 7 green, 2 advisory,
and 3 failing stages (`lint`, `defect_lint`, `override`). The first repaired
aggregate at `checks/after-1/` narrowed this to one real defect: generated target
counts were `4..6`, too far from canonical median 2. That failed iteration is kept.

## Final design

The generator now uses the exact local one-pass rule and six observable axes. A
six-slot cyclic schedule anchors `(6,8,palette 3)`, `(7,8,palette 4)`, and
`(6,9,palette 3)` while alternating richer scenes. Connected scenes contain a
same-color component with two local targets, a mixed-color near-match, and a cell
that a repeat-until-stable rival would fill only on a later pass. Repeated colors
across separated motifs refute per-color and exact-three-cells shortcuts.

The target-count range was reduced test-first to `3..6` so the generator remains
near the canonical `2..3` examples without forcing every lesson to be trivial.
`target_count=3, corner_diversity=4` and the joint
`target_count=3, color_count=3, layout_mode=connected` are structurally
impossible and declared. Default values are adjusted only when needed so each
single-axis override is still exact and independently usable.

## Verification highlights

Final generator SHA-256:
`788832612d5ab93e59f99522fd2b89e72e8d1d2ca7776779f272c13f22d08cf5`.

- Final inherited battery: 12/12 green (`checks/after-2/`).
- Portable task tests: 11/11 (`checks/task-tests-final/`).
- Focused source-bound probe: 864/864 strict generated scenes, 864 unique
  inputs, 36/36 cyclic lesson windows, zero failures
  (`checks/focused-semantic.json`).
- Production lesson census: 300/300 lessons materialized, 1,200/1,200 unique
  pair inputs, zero ambiguity/errors; every declared rival refuted in 100/100
  lessons in each band (`checks/lesson-census-final.json`).
- Post-repair visible solve passed all 3 demonstrations in one genuine revision;
  earlier rule exposure is declared `yes` and reference consultation `no`.

## Limits

The finite rival set is not a proof of universal identifiability. Generated
width begins at 8, so the canonical 7×7 profile is accepted by validators but is
not an ordinary draw; the schedule instead covers the other three canonical
size/palette profiles. Approval and training admission remain maintainer-owned.

## 2026-10-03 — optional rotated-query observation

A relocated shared-tool smoke produced two original three-demo/one-query lessons with zero ambiguity, but one of eight all-query rotations removed the sole counterexample to bbox completion, color agreement and repeated-application rivals. This is a finite observation, not a failure of the two production lessons. Exact source, seeds and query indices are in `evidence/maintainer-query-rotation-20261003.json`. Do not assume all query positions are interchangeable; recheck if changing lesson assembly. Generator source and authority are unchanged.
## Current reviewer considerations

Source SHA-256: `788832612d5ab93e59f99522fd2b89e72e8d1d2ca7776779f272c13f22d08cf5`.

# Decisions for 78f3cf31c4bf

## D1 — Preserve the canonical rule; change only the teaching distribution

**Input choice.** Keep the canonical rule exactly: inspect every 2×2 window in
the original input, and fill the sole zero only when the other three cells are
the same nonzero color.

**Rationale.** All four canonical pairs and the existing ordinary draws agreed
with this rule. The failure was weak curriculum and contract metadata, not an
oracle mismatch. `RULE_HASH = "4954a1b1ccb4"` now pins the selected source.

**Alternatives rejected.** I did not rewrite Racket, change scan order, use
newly filled cells, or interpret motifs as connected components. Those variants
would either alter authority or preserve canonical-fitting shortcuts.

**Probe/failure mode.** Real-rule smoke and authority sync are green in
`checks/after-2/`. The exact closure counterexample is retained under
`checks/question/78f3cf31c4bf/`.

## D2 — Replace decorative/dead knobs with six exact observable axes

**Input choice.** Expose `grid_h`, `grid_w`, `target_count`, `color_count`,
`layout_mode`, and `corner_diversity`; reject unknown keys; implement
`observe_overrides` and mutation-sensitive validation.

**Rationale.** Each axis changes an observable property of the returned grid and
is useful for curriculum coverage. The baseline's `palette_kind`, singleton
`position_bias`/`density`, overlapping texture alias, and independently claimed
palette counts were not exact contracts.

**Alternatives rejected.** I did not keep fake axes as “diagnostic” because they
were not needed. I also removed production texture degenerates instead of
letting no-op or overlapping scenes leak into ordinary lessons.

**Probe/failure mode.** The final override stage is green. Two structurally
impossible joint tuples are declared: `(target_count=3, corner_diversity=4)` and
`(target_count=3, color_count=3, layout_mode=connected)`. Every single-axis
request remains realizable by adjusting only unrequested defaults.

## D3 — Use a six-slot cyclic lesson schedule

**Input choice.** The first three slots anchor exact public profiles
`6×8/palette 3`, `7×8/palette 4`, and `6×9/palette 3`; later slots expand size
and geometry. Every three consecutive examples include a connected multicolor
control and repeated-color evidence.

**Rationale.** Production lessons use three demonstrations. A cyclic schedule
makes the semantic guarantee lesson-level rather than merely distribution-level.

**Alternatives rejected.** Pure random sampling could have high witness frequency
while still emitting ambiguous three-demo windows. A schedule of only canonical
isolated motifs would preserve all five named shortcuts.

**Probe/failure mode.** `workspace/review_probe.py` rotates 36 consecutive lesson
starts and iterates the live rival registries. The shared production census then
materialized 100 lessons per band with zero ambiguity.

## D4 — Add connected, repeated-color, mixed-color, and closure controls

**Input choice.** Connected modules contain two legitimate local windows within
one component. Multicolor connected modules reserve a mixed-color near-match and
a second-pass closure trap. Isolated modules deliberately reuse colors.

**Rationale.** Together these separate the true rule from component-bbox
completion, one-completion-per-color, exact-three-cells-per-color,
ignore-color-agreement, and repeat-until-stable rivals—all of which fit the
canonical pairs.

**Alternatives rejected.** Merely adding more isolated L-trominoes, larger grids,
or more colors would increase surface diversity without changing semantic
identifiability.

**Probe/failure mode.** First witnesses and counts are stored in
`checks/focused-semantic.json`; all five rivals fit 4/4 canonical pairs and are
refuted in every production lesson in `checks/lesson-census-final.json`.

## D5 — Bring target counts near the canonical distribution

**Input choice.** Generate 3..6 targets while accepting canonical 2..3 target
inputs in the strict validator.

**Rationale.** The first repaired draft generated only 4..6; defect lint correctly
flagged canonical median 2 as outside the generated range even with tolerance.
The test-first change to include three-target anchors removed that defect while
retaining enough structure for adversarial controls.

**Alternatives rejected.** Generating two-target scenes across the full Cartesian
axis matrix would create many impossible color/layout/corner combinations and
weaken lessons. Rejecting the lint finding as cosmetic would leave a genuine
canonical-coverage gap.

**Probe/failure mode.** The failed aggregate is preserved at `checks/after-1/`;
`checks/defect-after-2/` and the final 12-stage aggregate are green.

## D6 — Leave reusable, source-bound verification

**Input choice.** Add eleven portable task tests plus
`workspace/review_probe.py` and usage notes.

**Rationale.** Future edits need checks that load the selected sibling source,
bind reports to its SHA-256, discover current rival declarations rather than a
stale name list, verify canonical shortcut fit, and test cyclic lesson windows.

**Alternatives rejected.** Tests importing private `scripts.*` helpers were not
portable in direct reviewer runs. The suite uses the public `reviewer_support`
API instead.

## D7 — Known limitations

The declared rivals are a finite adversarial set, not a proof of universal ARC
induction. Ordinary generation starts at width 8, so the canonical 7×7 input is
accepted but not sampled; the other three canonical size/palette profiles are
explicit anchors. The generator remains unapproved/provisionally safe until
maintainer intake independently replays the returned source.
