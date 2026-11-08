# Working notes: 892ae3bfe537

## 2026-10-03 review

The selected `2.0.1` baseline was not source-bound to its authority and did not
cover the canonical task distribution. It lacked `RULE_HASH`, advertised inert
and contradictory axes, accepted unknown keys, failed 7,790 override checks,
produced zero exact canonical profiles in 60 draws, omitted vertical/horizontal
pairs from ordinary generation, allowed malformed “degenerate” textures through
its own checker, and declared no semantic contract. The before battery command
was attempted; it exceeded the wrapper window after preserving decisive
stage-level evidence.

The Racket program was not the defect. Its selected authority remains pinned at
`5b511829e91b`, solves all canonical pairs, and passed source/execution parity.
No Racket source was edited.

The generator was rewritten as `3.0.0` around only three live, observable axes.
A constructive slot layout supports the full `grid_h=6..10`, `grid_w=8..10`,
`n_pairs=2..3` Cartesian product. Every default lesson includes one area pair,
at least one collinear pair, a solid rectangle interior, disjoint boxes, and
exactly two cells per foreground color. Reflections and square-grid transposition
add layout variety without changing the grammar. Band defaults anchor every
canonical profile; unbanded draws cycle across all three instead of collapsing
to one shape.

The semantic contract names three rivals: diagonal-only, line-only, and
border-only. Corresponding witnesses fire on every generated input, and a
lesson check rejects any rival that survives all demos. The reusable workspace
probe tests 100 overlapping two-demo lessons in each band using 102 unique base
inputs per band; every declared rival disagrees on all 102 inputs and no lesson
has a survivor. This is finite source-bound evidence, not a universal induction
claim.

Regression tests cover all canonical pairs, every advertised override
combination across all bands, invalid and unknown overrides, deterministic
replay, the unbanded profile cycle, structural impostors, all semantic branches,
and lesson identifiability. Final generator SHA-256:
`60d4eb6dced78460a3c15c9612820033b9c7ae1d368a983ede33aaafb362a894`.

Known limitation: the curriculum intentionally teaches disjoint boxes with one
area pair and one or two line pairs. The authority can mechanically process
other count-two arrangements, including multiple area boxes, but those are not
claimed as part of this training grammar. Because every lesson carries all
three decisive witnesses, semantic coverage is strong but morphological
co-occurrence is less varied than a broader curriculum would be.
## Current reviewer considerations

Source SHA-256: `60d4eb6dced78460a3c15c9612820033b9c7ae1d368a983ede33aaafb362a894`.

# Design and review decisions for 892ae3bfe537

## D1 — Leave the Racket authority unchanged

**Choice.** Keep the canonical program byte-for-byte unchanged and pin
`RULE_HASH = "5b511829e91b"` in the generator.

**Rationale.** The selected authority solves all three canonical pairs, the rule
smoke applied it successfully to 120/120 generated inputs, and authority sync
reports execution parity across the selected and archival texts. The defects
were in the sampler and public contract, not the transformation.

**Alternatives considered.** Simplifying the Racket code or changing its
handling of count-two colors would create unnecessary authority churn and risk
changing canonical behavior.

**Evidence.** `checks/after_final_battery/checks/892ae3bfe537_after_rule_smoke.log`
and `checks/after_final_battery/checks/892ae3bfe537_after_authority_sync.log`.

## D2 — Replace the nine-axis surface with three exact axes

**Choice.** Advertise only `grid_h=6..10`, `grid_w=8..10`, and `n_pairs=2..3`.
Reject unknown keys, non-integral values, and out-of-range values loudly.

**Original state.** The baseline advertised inert aliases, singleton controls,
contradictory palette counts, and negative textures. It accepted an unknown key
and produced 7,790 findings over 84,870 override draws, with 32,340 undeclared
multi-axis rejections accepted by legacy policy.

**Rationale.** Every retained axis is directly recoverable from pixels and every
Cartesian combination is constructible. Removing false controls is safer than
inventing arbitrary semantics for them.

**Rejected alternatives.** Keeping `palette_kind`, `palette_size`,
`n_distinct_colors`, `density`, `position_bias`, or `texture` as aliases would
leave multiple names for the same observable quantity or preserve non-lawful
fixtures as ordinary data.

**Probe/failure mode.** The task-local tests enumerate representative boundaries
for all three axes across all four band values. The final override gate accepted
3,960/3,960 draws over 44 cases and three bands. Evidence:
`checks/before_override/` and `checks/after_final_battery/checks/892ae3bfe537_after_override.log`.

## D3 — Anchor every band to a canonical profile

**Choice.** Use deterministic defaults `(6,9,2)` for easy, `(8,8,2)` for medium,
and `(10,10,3)` for hard; the tuple records height, width, and foreground pair
count. Unbanded draws cycle through those three profiles by seed/sample index.

**Rationale.** The canonical grids have palette profiles `(6,9,3)`, `(8,8,3)`,
and `(10,10,4)` when background is counted. The baseline hit none of them in 60
draws and had no hard-band support. Exact anchors make all bands source-linked
without requiring probabilistic luck.

**Alternative considered.** Randomly sampling the full dimension ranges would
increase marginal variety but could again miss a canonical profile in the
small training/check windows. The retained transformations provide layout
variation while the band shapes stay interpretable.

**Probe/failure mode.** A late diversity probe revealed that an unbanded fallback
collapsed to 8×8. A failing regression test was added first; the fallback was
then changed to cycle all profiles. Final profile floor is 60/60 exact and
60/60 in-envelope, while diversity reports three shapes and no flags. Evidence:
`checks/iterations/unbanded_profile_red.log`, `checks/after_final_battery/checks/892ae3bfe537_after_profile_floor.log`, and
`checks/after_final_battery/checks/892ae3bfe537_after_diversity.log`.

## D4 — Put one area pair and one or two collinear pairs in every lesson

**Choice.** Each input has exactly one pair spanning rows and columns and one or
two horizontal/vertical pairs. Every pair's bounding box contains at least
three cells.

**Rationale.** Canonical examples require both genuine rectangles and degenerate
line boxes. The baseline generated only non-collinear pairs, so “fill only
rectangles” could fit all ordinary data. Co-locating both branches in every
input refutes diagonal-only and line-only shortcuts even in a two-demo lesson.
A minimum 3×3 area box also exposes a true interior and refutes border-only.

**Alternatives considered.** Scheduling branch types across separate examples
would create more morphology variety, but a sampled lesson could omit a decisive
branch. Multiple area rectangles were not needed to identify the rule and make
constructive non-overlap harder on 6×8 grids.

**Probe/failure mode.** The semantic gate reports all three witnesses firing on
600/600 draws and verifies all three rival claims. The retained lesson probe
reports 100/100 identifiable lessons per band and each rival disagreeing on
102/102 unique base inputs per band. Evidence:
`checks/after_final_battery/checks/892ae3bfe537_after_semantic_gate.log` and
`checks/final_lesson_probe/lesson_probe.json`.

## D5 — Require disjoint bounding boxes

**Choice.** Construct pair boxes in reserved slots and reject any overlapping
boxes in `self_check`.

**Rationale.** Overlap introduces paint-order ambiguity between colors, which is
not present in the canonical task and creates labels that depend on iteration
order rather than the intended independent per-color rule.

**Alternative considered.** Allowing overlaps with an explicit priority would
teach an extra rule unsupported by the source. The baseline's
`overlapping_bboxes` texture was therefore removed rather than legalized.

**Probe/failure mode.** A targeted test builds crossing boxes and requires an
overlap error. The constructive sampler has no rejection loop and cannot
silently omit a pair.

## D6 — Use constructive slots, then symmetry transforms

**Choice.** Place an area box in a left interior slot, reserve edge columns/a
bottom row for line pairs, then apply row/column reflection and square-grid
transposition.

**Rationale.** This guarantees the full override domain at the minimum 6×8
canvas, avoids stochastic retries, and keeps all requested pairs. Symmetries
reduce absolute-position shortcuts without threatening disjointness.

**Alternatives considered.** The baseline's repeated random placement could
exhaust attempts and silently return fewer pairs. A general packing solver would
be more complex than this small domain requires.

**Limit.** Line pairs remain near transformed outer bands because of the slot
construction. Reflections and 8×8 transposition diversify which side is used,
but the curriculum is not uniform over all lawful placements.

## D7 — Make `self_check` describe the training grammar, not every program input

**Choice.** Validate dimensions, integer ARC colors, two or three colors, exactly
two cells per color, exactly one area pair, the remaining line pairs, minimum
box area, and pairwise box disjointness. `strict_canonical_like` delegates to
that same grammar.

**Rationale.** A checker that merely counts color occurrences let blank and
ambiguous baseline fixtures pass. The new checker is intentionally narrower
than the mechanical Racket domain and exactly matches what the sampler claims.

**Alternative considered.** Accepting every input the Racket program can process
would make strict support easy but would not distinguish high-quality training
examples from malformed or ambiguous ones.

**Limit.** Color permutation is a lawful invariance, so color-swap mutations
correctly pass. Final mutation sensitivity is 49/61 overall, with every blank,
missing-color, and duplicate-row destructive class rejected as applicable.

## D8 — Use an independent Python oracle only for tests and rival execution

**Choice.** `_fill_pairs` independently implements the bbox transformation for
canonical parity tests and executable rivals; the Racket program remains the
label authority.

**Rationale.** Tests need a cheap, inspectable expected transformation, but
training labels must remain bound to the canonical authority. Rule smoke and
canonical parity guard against drift between the mirror and Racket.

**Alternative considered.** Calling Racket from every unit test would be slower
and make small structural tests harder to isolate.

## D9 — Set `EXAMPLES_NEEDED = 2`

**Choice.** Assemble two-demo lessons.

**Rationale.** Every single generated input already contains all three decisive
semantic witnesses, so two demos provide redundancy rather than branch coverage.
The retained 100-lesson probe found no declared survivor in any band.

**Alternative considered.** Keeping the baseline value of three would consume
more context without adding a missing branch. One demo would likely be enough
for the declared rivals but gives no replay redundancy.

## D10 — Preserve finite-evidence limits explicitly

**Choice.** Report exact seeds, sample indices, denominators, source hashes, and
window overlap; do not call finite rival checks universal induction.

**Rationale.** A generated curriculum can still contain undeclared shortcuts.
The two unrelated audits found such confounds even in previously green
semantic contracts. For this task, the strongest remaining restriction is the
fixed co-occurrence pattern: one area pair plus line pair(s) in every input.

**Reusable tool.** `repo/generators/892ae3bfe537/workspace/probe_lessons.py`
replays 100 overlapping lessons per band from the generator's actual declared
competitor set and writes a source-bound JSON report.
