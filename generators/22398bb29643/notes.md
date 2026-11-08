# Working notes: 22398bb29643

## Intended rule and authority

The unchanged canonical Racket rule finds every nonzero 4-connected component,
sorts components by bounding-box top row and then left column, and emits one row
containing one color per component. Repeated colors must therefore be repeated
in the output. The reviewed authority is pinned as `RULE_HASH = "bea915e9e998"`.
No Racket source was changed.

## Source transition

The issued generator source was
`c07faac1a4a2ba7f7ae54234e0d4dd4f9f0391ac769aabd99e81a01b92556c01`.
The final generator source is
`449fd8beeae0543c5cc3b21bebb446ce14ab10f9dd94088932bd98851c828563`
(version `3.0.0`). The prior source advertised several controls that were
constant, ignored, or invalid in most combinations; it also lacked a rule-hash
pin and an executable semantic contract. Its baseline battery finished with 7
green, 2 advisory, and 3 failed stages.

## Current construction

- Public exact axes are only `grid_h` (`9..12`), `grid_w` (`9..14`), and
  `components` (`3..6`). Unknown keys, booleans, non-integers, and out-of-range
  values are rejected rather than silently recorded.
- Components are placed constructively in separated `3×2` or `2×3` slots. Each
  generated scene includes sizes 3, 4, and 5; additional components also use
  size 3–5. This avoids capped rejection loops and under-filled requests.
- A ten-profile schedule covers the five canonical `(height, width,
  nonzero-color-count)` profiles. Even slots preserve exact canonical color
  support; odd slots keep the same component count but repeat a component color.
- Difficulty bands use independent keyed palette draws while preserving the same
  task law and profile support.

## Shortcut decision and prior review lead

The retained source-bound audit from `review-9dff8738d2938418:v0001` identified
the strongest canonical-fitting shortcut: sort components but emit each color
only once. All five canonical pairs use one component per nonzero color, so they
do not distinguish that rival. I used that audit as a lead and made it an
executable `CANONICAL_SHORTCUTS` / `LESSON_COMPETITORS` rival named
`deduplicate_component_colors`, with a `repeated_component_color` witness.

The exact retained witness is
`counterexamples/deduplicate-component-colors.json`: seed 17, sample index 1,
medium difficulty gives intended output `[7, 3, 2, 2, 6]`, while the shortcut
gives `[7, 3, 2, 6]`. The generator alternates canonical and witness profiles,
so every four-pair lesson assembled from three demonstrations and one query
contains repeated-color evidence under every query rotation.

## Verification

- Final twelve-stage battery: 12/12 green under required rotation
  identifiability; see `checks/after/`.
- Exact override matrix: 7,290/7,290 successful draws, including 2,430/2,430
  global combinations.
- Strict canonical grammar: 600/600 generated draws and 5/5 canonical inputs.
- Semantic smoke: 286/600 witness hits, 60/60 checked rival disagreements,
  12/12 production lessons identifiable, and 0/48 ambiguous rotations.
- Larger census: 300 lessons, 1,200 labeled pairs, 1,200 query rotations,
  0 production or rotation ambiguities, and 1,200 exact unique inputs; see
  `checks/lesson-census.json`.
- Task-local regressions cover canonical parity, exact controls, constructive
  morphology, schedule windows/rotations, semantic rivals, and the retained
  counterexample.

## Known limits

The semantic evidence is finite and tests the declared deduplication rival; it
is not a proof against every possible hypothesis. Generated components are
monochrome, separated by background, and drawn from a bounded `3×2`/`2×3`
polyomino family. Those restrictions match the intended generator grammar but
do not cover touching multicolor objects or arbitrary larger shapes.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-9dff8738d2938418:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `c07faac1a4a2ba7f7ae54234e0d4dd4f9f0391ac769aabd99e81a01b92556c01`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted source SHA 449fd8beeae0543c5cc3b21bebb446ce14ab10f9dd94088932bd98851c828563 turns the prior deduplicating-color shortcut lead into an executable rival/witness and a schedule guaranteeing repeated-color support. tests/test_semantic_contract.py, tests/test_schedule_morphology.py and counterexamples/deduplicate-component-colors.json retain regressions. Reviewer reports 300 production lessons and 1200 query rotations with zero ambiguity after fresh patch replay. Explicitly resolve this original missing-guarantee finding on reviewer-reported evidence; no maintainer rerun.

### Assessment or prior finding

## 22398bb29643

Plausible canonical shortcut: **sort distinct nonzero colors by the top row of
their first component, emitting each color only once**. All five canonical
inputs have exactly one component per nonzero color, so this deduplicating rule
matches every canonical output even though the intended rule emits one entry per
component.

The current generator does emit a useful counterexample. With
`seed=0`, `sample_index=0`, `difficulty="easy"`, the ordered component
descriptors `(color, size, top, left)` are:

```text
(5, 2, 2, 3)
(7, 2, 2, 5)
(3, 2, 8, 2)
(3, 1, 10, 8)
```

The intended output is `[5, 7, 3, 3]`; the deduplicating shortcut gives
`[5, 7, 3]`. Thus the canonical set is ambiguous on repeated-color components,
but this default generated case correctly refutes the shortcut. A future
semantic contract should name this rival and guarantee at least one
repeated-color witness per lesson rather than relying on random color collision.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `449fd8beeae0543c5cc3b21bebb446ce14ab10f9dd94088932bd98851c828563`.

# Decisions for 22398bb29643

## D1 — Keep the canonical rule unchanged and pin it

**Original state:** the generator omitted `RULE_HASH`, although the selected
Racket authority was stable and passed rule smoke.

**Decision:** add `RULE_HASH = "bea915e9e998"` and a task-local Python mirror
used only for review tests and semantic probes. Do not edit the Racket rule.

**Why:** the defect was in input generation and lesson teaching, not label
execution. Canonical parity was checked on all five labeled pairs.

**Failure mode avoided:** changing labels to accommodate a weak sampler, or
allowing future authority drift to go unnoticed.

## D2 — Remove false controls instead of pretending to implement them

**Original state:** `palette_kind`, `palette_size`, `position_bias`,
`n_distinct_colors`, `density`, and `texture` were advertised despite being
ignored, constant, redundant, or invalid in most combinations.

**Decision:** expose only exact integer controls that are observable in the
returned grid: `grid_h`, `grid_w`, and `components`. Reject unknown keys,
booleans, non-integers, and out-of-range values.

**Alternatives rejected:** preserving compatibility by accepting and ignoring
old names; inventing cosmetic meanings for controls unrelated to this task.
Both would leave the override contract misleading.

**Evidence:** final override gate passed 7,290/7,290 draws, including all 2,430
global combinations.

## D3 — Use constructive separated slots

**Original state:** placement was best-effort and could under-fill requested
scenes or make combinations infeasible.

**Decision:** choose a feasible `3×2` or `2×3` slot lattice and sample distinct
origins. Every accepted `(height, width, component-count)` combination is
constructive.

**Alternatives rejected:** longer capped rejection loops and post-hoc clipping.
Those can silently shorten a scene and make recorded controls false.

**Known limit:** this intentionally bounds generated morphology to separated
polyominoes that fit those slots.

## D4 — Match canonical morphology without copying canonical grids

**Original state:** generated objects were too small relative to the canonical
range and profile support was weak.

**Decision:** every default scene contains component sizes 3, 4, and 5; remaining
objects also use 3–5 cells. The schedule covers all five canonical dimension and
nonzero-color-count profiles while positions, shapes, colors, and orientation
remain generated.

**Alternative rejected:** replaying canonical inputs or opting out of the
profile floor. The task supports constructive variation at canonical scale.

## D5 — Alternate canonical and repeated-color profiles

**Prior review lead:** `review-9dff8738d2938418:v0001` showed that color
deduplication fits all canonical pairs and recommended guaranteed repeated-color
teaching evidence.

**Decision:** even schedule slots preserve exact canonical color support; odd
slots keep the same dimensions and component count but use one fewer distinct
color. This produces a direct witness without changing scene complexity.

**Alternatives rejected:** relying on random color collision; making every scene
a repeated-color case; adding extra objects solely for the witness. The selected
schedule preserves both canonical support and a guaranteed discriminator.

## D6 — Make the rival executable

**Decision:** declare `deduplicate_component_colors` in
`SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`; declare
`repeated_component_color` in `SEMANTIC_WITNESSES`; bind them with
`WITNESS_RIVALS`; and set `EXAMPLES_NEEDED = 3`.

**Probe:** seed 17, sample index 1, medium difficulty gives intended output
`[7, 3, 2, 2, 6]` and rival output `[7, 3, 2, 6]`.

**Limitation:** this is a finite declared-rival contract, not a proof against
all possible hypotheses.

## D7 — Guarantee query-rotation teaching support

**Decision:** structure each four-sample window as two canonical profiles and
two repeated-color witnesses. With three demonstrations and one held-out query,
every rotation retains at least one witness among the demonstrations.

**Evidence:** final smoke found 0/48 ambiguous rotations; the larger census found
0/1,200 ambiguous rotations across 300 lessons.

**Rejected claim:** do not declare a fixed `LESSON_SCHEDULE_PERIOD` merely to
silence tooling. The explicit profile schedule is tested directly, while the
larger census is retained separately.

## D8 — Preserve band semantics without creating band-specific rules

**Decision:** all bands share the same dimensions, component law, and profile
schedule. Band-specific keyed palette draws and a fixed first color make the
realized instances differ without changing what must be inferred.

**Failure mode avoided:** byte-identical bands or a difficulty cue that selects a
different transformation.

## D9 — Audit-only targets remain unchanged

`b46564e50781` and `e64c021e29ad` were inspected as findings-only targets. The
former has a reproduced validator defect; the latter had no new issue found and
49/49 portable task tests passed. No files under either generator were edited.
