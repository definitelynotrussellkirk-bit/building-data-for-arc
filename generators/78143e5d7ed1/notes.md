# Current design notes: 78143e5d7ed1

## Intended rule

On a zero background, extract each single-color 4-connected component, take its
tight bounding-box crop, and sort the crops lexicographically by
`(cell count, bbox height, bbox width, color)` ascending. Pack the crops
left-to-right with one zero column between them and bottom-align them to the
tallest crop. The selected canonical Racket program remains the sole label
authority; `RULE_HASH` is pinned to `d87cff5947e7`.

## Current sampler, version 2.1.0

- Exact public axes are `grid_h=9..14`, `grid_w=12..20`, `n_objs=3..4`,
  `palette_kind={low,high,mixed}`, and
  `tie_profile={area,height,width,color}`.
- Every generated input has three or four distinct-color, single-color
  polyominoes with a one-cell Chebyshev moat. Crops contain 3..7 cells and at
  least one crop is non-rectangular.
- Canonical-scale anchors cycle through the four actual canonical profiles
  `(height,width,n_colors) = (9,12,4), (10,12,4), (10,14,4), (11,13,4)`.
- Unknown override keys are rejected. `sample_index` must be a nonnegative
  integer and booleans are rejected rather than treated as integers.

## Reversed lesson-schedule decision

Version 2.0.0 assigned one sort-key witness to each profile. A retained audit
from `review-6796555a398bce98:v0001` was used only as a lead and then reproduced
against baseline SHA-256
`57c14bb49e91ea3f908c5ac162b5593fb3574325f62469b0f09fd7ba937fa645`.
For seed 0, medium, start 0, the profile sequence was
`area,height,width,color,area`; when the sole height profile was held out as the
query, a lawful `(area,width,color)` rival fit all four demonstrations and
changed the query answer. The same source silently ignored `typo_axis=123`.
The retained exact counterexample is under
`counterexamples/review-6796555a398bce98-v0001/`.

Version 2.1.0 replaces the one-key profiles with paired evidence:

- `area` demonstrates `{area,height}`;
- `height` demonstrates `{height,color}`;
- `width` demonstrates `{area,width}`;
- `color` demonstrates `{width,color}`.

Any three distinct profiles cover all four lexicographic keys. Therefore every
four demonstrations retained from five consecutive sample indices cover area,
height, width, and color under every query rotation. Color assignment and source
placement are deterministic with respect to the intended rebuttal, while colors,
positions, canvas sizes, and palettes remain keyed and varied.

## Semantic contract

`EXAMPLES_NEEDED=4`. `lesson_identifiable` checks aggregate key evidence,
canonical labels, query validity, and thirteen executable rivals:
source order; area-only and area-height prefixes; omission of each of the four
sort keys; bbox-area, color-first, descending, top-aligned, no-gap, and
filled-bbox-crop alternatives. Witnesses are tied to measured output
disagreements with named rivals; merely containing a nominal feature is not
counted as evidence.

Final source SHA-256 is
`79d9f9c3243d6e353277e0a9ef0b722592269648e151658af56853787712813e`.
The 12-stage after battery is all green. A required-rotation semantic smoke test
found 12/12 production lessons identifiable and 0/60 ambiguous rotations. A
100-lessons-per-band census materialized 300 five-pair lessons / 1,500 unique
inputs and found 0/300 ambiguous production lessons and 0/1,500 ambiguous query
rotations, with no hook or scoring errors. The focused portable review suite has
9 passing tests and exhausts three bands, two seeds, four cyclic starts, five
query positions, and every declared rival.

## Authority and limits

No canonical pair or Racket authority changed. Finite declared-rival checks do
not prove unique induction against every possible hypothesis. The canonical
examples alone leave several key-omission rivals viable, so generated lesson
evidence remains essential. The sampler intentionally stays within 3..7-cell,
4x4-or-smaller crop families and omits generated color 5; broadening either
choice needs fresh exact-control and semantic coverage checks.

The inherited root fixture now resolves its canonical ledger through
`reviewer_support.find_root` and `canonical_path`, so the official portable
`task_tests` stage executes rather than stopping at preflight. The final
portable target suite passes 25 tests. This repair changes tests only; the
production generator and canonical Racket authority remain byte-identical.
## Current reviewer considerations

Source SHA-256: `79d9f9c3243d6e353277e0a9ef0b722592269648e151658af56853787712813e`.

# Decisions: 78143e5d7ed1

All final measurements refer to generator version `2.1.0`, SHA-256
`79d9f9c3243d6e353277e0a9ef0b722592269648e151658af56853787712813e`,
and unchanged canonical rule hash `d87cff5947e7`.

## D1 — Reproduce the retained audit rather than trust it

**Prior choice/rationale:** the imported review index carried an unresolved finding from `review-6796555a398bce98:v0001`; its original rationale was externally reported.

**Decision:** use that return only to choose a probe, then run the exact reproducer against the selected baseline bytes before designing a repair.

**Evidence:** `checks/before-audit-reproducer/78143e5d7ed1/stdout.json` reproduces the source hash, seed, start, profile sequence, four-demo fit vector, query disagreement, and silently accepted unknown key.

**Limit:** the prior Racket receipt is retained with the counterexample, but the current repair’s acceptance rests on fresh final-source checks, not the prior reviewer’s conclusion.

## D2 — Keep the canonical Racket rule unchanged

**Prior choice:** the selected generator was already pinned to the synchronized rule `d87cff5947e7`.

**Alternatives considered:** modify the Racket ordering rule; narrow the rule to omit height; or repair only generated evidence. The first two would contradict canonical labels and the assignment’s authority hierarchy.

**Decision:** repair sampling, lesson contracts, and tests only. No canonical pair or Racket source changed.

**Evidence:** final `rule_smoke`, `racket_lint`, and `authority_sync` stages are green; execution parity passes.

## D3 — Replace single-key profiles with paired evidence

**Prior choice/rationale:** version 2.0.0 scheduled `area,height,width,color`, one key per pair, so the fixed four-demo lesson covered all keys only when the query stayed in its intended position.

**Alternatives considered:**

1. Declare query order fixed and forbid rotation.
2. Increase to five demonstrations plus one query.
3. Resample until all four keys appear after a query is selected.
4. Add more schedule slots, one for every pair of keys.
5. Make each of four existing profiles carry a complementary second key.

**Decision:** choose option 5. It preserves four demonstrations, deterministic generation, and the existing four-slot schedule while making any four-of-five rotation safe.

**Pairing:** `area→{area,height}`, `height→{height,color}`, `width→{area,width}`, `color→{width,color}`. Any three distinct profiles cover all four keys.

**Failure modes checked:** accidental source/color order could let an omitted-key rival match despite nominal geometry. `_assign_profile_colors` and placement ordering deliberately oppose the relevant rivals; focused tests assert actual output disagreement, not just feature presence.

## D4 — Define lesson success by executable rivals and aggregate evidence

**Prior choice:** the baseline semantic contract did not include the discovered key-omission rivals, and the hook could reject rotations merely because a named profile was absent even when equivalent evidence remained.

**Decision:** compute sort-key evidence directly from component comparisons, aggregate it across demonstrations, and add omission rivals for area, height, width, and color. Also add a filled-bbox rival because sparse crops distinguish tight extraction from rectangle filling.

**Alternatives considered:** check only profile labels; check only the four key omissions; or rely only on the generic semantic gate. Profile labels are an implementation detail, four omissions miss spatial/alignment shortcuts, and the generic gate did not synthesize the relevant sort-key rival.

**Evidence:** strict smoke: 12/12 lessons and 60/60 rotations; large census: 300/300 lessons and 1,500/1,500 rotations with no declared-rival ambiguity.

**Limit:** the rival set is finite. It demonstrates resistance to named plausible shortcuts, not universal identifiability.

## D5 — Make semantic witnesses causal

**Prior choice:** a witness could be interpreted as “this feature exists,” even when removing that feature would not change the answer.

**Decision:** every witness is now implemented as a measured disagreement between the canonical solver and a named rival, with `WITNESS_RIVALS` recording the mapping.

**Reason:** training evidence should establish that the observation matters to the prediction. Presence without changed output is weak evidence.

**Probe:** `test_semantic_witnesses_name_measured_rival_disagreements` searches generated grids and asserts each mapped rival differs from the canonical output.

## D6 — Reject malformed controls before generation

**Prior behavior:** unknown keyword overrides were ignored; Python booleans were accepted as integers; `-1` was accepted as a sample index.

**Decision:** reject unknown override names with `ValueError`, non-integer/boolean sample indices with `TypeError`, and negative indices with `ValueError`.

**Alternatives considered:** silently ignore extras for forward compatibility; coerce booleans; normalize negative values modulo the schedule. All three make replay provenance ambiguous and hide caller errors.

**Evidence:** focused red/green tests plus the final override gate’s 21,780 legal calls and strict unknown-key probe.

## D7 — Anchor canonical support to observed canonical profiles

**Prior choice/rationale:** version 2.0.0 periodically forced `(9,12)`, `(10,13)`, and `(11,14)`. Only the first is an exact canonical profile, so the pinned hard-band sequence could miss exact support entirely.

**Decision:** cycle the four actual canonical dimension pairs `(9,12)`, `(10,12)`, `(10,14)`, `(11,13)` with three objects.

**Alternatives considered:** loosen the profile gate to envelope-only support; increase random probability; or pin one canonical pair in every band. Envelope-only support weakens the required check, random support is unstable, and a single pair underrepresents the canonical set.

**Evidence:** final profile floor records 5 exact hits in each band’s 20 pinned draws.

## D8 — Preserve existing bounded shape and palette choices

**Current choice:** retain 3..7-cell connected crops, maximum 4×4 crop dimensions, three/four components, and generated palettes that do not use color 5.

**Reason:** these bounds are already compatible with canonical inputs, exact controls, and output-size constraints; changing them is unrelated to the reproduced lesson defect.

**Alternatives considered:** broaden arbitrary polyomino size, include color 5, or generate every validator-legal arrangement. Each would enlarge the distribution and require new overlap, packing-width, override, and semantic measurements.

**Known limit:** passing this review does not establish behavior over every input accepted by the Racket program.

## D9 — Make the portable fixture source-tree independent

**Observed defect:** `tests/test_generator_78143e5d7ed1.py` derived the canonical path from a fixed `Path.parents` depth, which points below the copied runtime root during `task_tests`.

**Decision:** use `reviewer_support.find_root(__file__)` and `canonical_path` while retaining the same assertions and canonical data. The separate rotation-contract tests remain in place.

**Result:** the official portable target suite now executes and passes 25/25 tests. No production or Racket authority bytes changed.

## D10 — Keep the post-repair solve independent of source knowledge

**Decision:** after final generator bytes were frozen, prepare a fresh visible-only episode, keep generator/rule/reference files closed during the solve, declare earlier exposure honestly, and stop after the first revision passed all four displayed examples.

**Reason:** a successful solve is useful only if its provenance is honest. Earlier generator work prevents calling it blind, but it can still demonstrate that the final examples visibly support the intended transformation.

**Evidence:** `solve/summary.json` and `solve/FINISHED_NOTES.md` bind the episode to the final generator hash.

## D11 — Leave both adversarial audit targets unchanged

**Decision:** treat `b88894a36787` and `4201f3b3ea1b` as findings-only targets. No source under either generator was edited.

**Reason:** the assignment requests adversarial review, not repair. Exact target source hashes, commands, and evidence are retained in `AUDIT.md` and `checks/audit/`.


## Native parametric sort-direction deliverable — 2026-10-25

The current task-local native adapter is under `workspace/parametric/` and keeps
`sort_direction=smallest_first` byte-identical to the canonical program.
`largest_first` reverses the complete `(cell count, bbox height, bbox width,
color)` lexicographic order before bottom-aligned packing. The family supports
2–6 demonstrations and exactly four setting-independent queries; every episode
ends with a structural 30×30 seven-component query touching all four boundaries.

A bounded audit covers both settings, seeds 0/17/97 and demonstration counts
2/3/6. Its first two demonstrations reject all 11 declared rivals, including
bbox-area ordering and omission of each sort key. Native qualification executed
40 protected-Racket labels. The causal witness replays the qualified
largest-first program against a bbox-area intermediate; the two final packed
grids differ. Status is reviewer-ready, with exact-source owner acceptance and
training admission explicitly not performed.
