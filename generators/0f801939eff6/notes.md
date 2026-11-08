# Working notes: 0f801939eff6

## Current rule and authority

The intended transformation is component-based, not color-frequency based: find every nonzero same-color 4-connected component, sort components by `(-area, color)`, and concatenate one run per component. The canonical Racket authority was not changed. `RULE_HASH = "cbb04236ecda"` pins the selected generator to that authority.

## Current native parametric proposal

`workspace/parametric/` adds `merge=none|2_into_1`; `none` preserves the exact
canonical program. The alternative recolors every 2 to 1 before recomputing
components, areas and rank. A protected-Racket wrong-order witness shows why
ranking the original components then recoloring is insufficient. Counts are
independent (2–6 demos, 1–4 queries), with matched inputs across settings and a
substantive 30×30/four-corner case under the inherent 30-cell output limit.
The initial two-demo lesson admitted local-cluster-only recoloring; an isolated
color-2 component in demo two now refutes it without increasing demo count.
The exporter pre-serializes exact private bytes before publishing any public file.
Current evidence: 80 focused tests; 72/72 bounded Python samples; native
qualification over both settings and seeds 0/17; 90 protected-Racket audit calls
plus a 10-call before/after teaching replay. See the prototype README and returned
`checks/0f801939eff6/{qualification-v3,audit-v3}/`, `teaching-repair.json`.
The next action is owner native qualification and fresh acceptance after source
integration. This proposal does not change canonical approval, add production
size overrides, establish universal identifiability, or activate training.

## Reversed baseline decisions

Version 2.1.3 generated one distinct color per component and effectively distinct component sizes. That made global per-color counting observationally equivalent to connected-component extraction and left the canonical color-frequency shortcut unchallenged. It also advertised controls that were clipped, dead, or silently ignored, and placement could omit intended objects. The current version replaces those choices rather than preserving them:

- The only public axes are observable pixels: `grid_h` 8..16, `grid_w` 11..18, and four-valued `scene_profile`. Every exact value works in every difficulty band; unknown or ill-typed overrides fail loudly.
- Construction always places all four requested components by finite backtracking with a one-cell separation halo. It never accepts a partial placement.
- Repeated-color profiles reuse one color on the largest and smallest disconnected components, so component-wise ordering differs from aggregating all cells of that color.
- Tie profiles contain exactly one equal-area pair. Their colors are assigned opposite row-major order, so the canonical ascending-color tie-break differs from a position tie-break.
- Component areas are selected constructively so the output row is wider than the input for every advertised width and remains within ARC's 30-cell bound.
- `self_check`, `strict_canonical_like`, `observe_overrides`, `rule_mirror`, executable witnesses/rivals, and `lesson_identifiable` make the contract directly testable.

## Lesson policy

`EXAMPLES_NEEDED = 3` and `LESSON_SCHEDULE_PERIOD = 4`. The profile order is:

1. `unique_distinct`
2. `repeated_distinct`
3. `unique_tie`
4. `repeated_tie`

Every cyclic three-demo window contains at least one repeated-color scene and at least one tie scene. The production policy is ordered; the retained large census also checks every query rotation of each materialized four-pair lesson.

## Evidence

- Source-bound shortcut and profile probe: `checks/final-shortcut-probe.json`. On source SHA-256 `1a0c005389f20e2b3ea5ea5697f9b5117ba0d8fd25b2c40c917fb3a038f6ac87`, color-frequency aggregation fits all 5 canonical labeled pairs, while 150/300 generated draws refute it; position tie-breaking is refuted by 150/300. All four profiles occur 75 times and all 300 inputs pass `self_check`.
- Large lesson census: `checks/lesson-census-final.json`. It materializes 300 lessons (100 per band), 1,200 unique labeled inputs, and 1,200 query rotations with zero declared-rival ambiguity, hook warning, scoring error, or materialization error.
- Focused regressions: `generators/0f801939eff6/tests/test_generator.py` and `tests/test_shortcut_probe.py`. The retained TDD red/green logs are under `checks/tdd-*`.
- Historical fixed counterexample: `counterexamples/review-ca62fa1453076264-v0001/retained/checks/audit_probes.json`.

## Known limits and open findings

The semantic claim is finite: it covers the two named plausible rivals, the declared four-step schedule, and the measured samples. It does not prove uniqueness against every possible hypothesis. Generated scenes always have four components and areas at most seven, although `strict_canonical_like` deliberately accepts the broader lawful canonical manifold. The deterministic schedule supports arbitrary cyclic starts, but downstream consumers must preserve three demonstrations; fewer demonstrations can leave a rival alive. No open blocker is known for the selected generator.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-ca62fa1453076264:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `5b5da4b3c309775141a66ba373bb4aa66aa8afbbba609c04d70ca0002b7965bb`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Specific global-color-count shortcut on 5b5da4b3c309 addressed by accepted 1a0c005389f2: disconnected same-color components and equal-area ties scheduled with executable rivals/witnesses. Reviewer reports 81 tests, 12/12 battery, 300 lessons/1200 rotations and 12 fixed lessons/48 rotations. Source-bound reviewer evidence, no independent rerun or arbitrary-hypothesis clearance.

### Assessment or prior finding

## 0f801939eff6

**Classification: reproduced shortcut / semantic distribution gap.**

I sampled 300 default generated inputs. All 300 had exactly one connected
component per color, all 300 had distinct component sizes, and a shortcut that
counts each color's total nonzero frequency and sorts colors by that count
matched the authoritative component-sorting rule on 300/300 cases. Thus the
generator does not force a learner to segment repeated-color disconnected
components. The target's `self_check` does not forbid the missing case.

A concrete 7x10 counterexample contains:

- a color-2 2x2 component (size 4),
- a color-3 horizontal component (size 3), and
- a disconnected color-2 singleton (size 1).

The canonical Racket authority outputs:

`[2, 2, 2, 2, 3, 3, 3, 2]`

because it orders **components** by size. The color-frequency shortcut outputs:

`[2, 2, 2, 2, 2, 3, 3, 3]`

because it combines both color-2 components into frequency 5. The canonical
Racket output, Python component mirror, shortcut output, full counterexample,
and 300-draw census are reproduced in `checks/audit_probes.json`.

A minimal distribution repair would occasionally reuse one color across two
disconnected components while preserving distinct component sizes, and add a
lesson-level competitor that aggregates by color. No target code was changed as
part of this findings-only audit.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-ca62fa1453076264-v0001/audit_assets.json), manifest SHA-256 `f497210bc07287334eb33840e3b6a1269244055b38252de96a7166f20ce53626`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `1a0c005389f20e2b3ea5ea5697f9b5117ba0d8fd25b2c40c917fb3a038f6ac87`.

# Decisions: 0f801939eff6

## D1 — Treat connected components as the unit, not colors

**Prior choice:** version 2.1.3 assigned a distinct color to every generated object. The original rationale is not recorded; likely it simplified labeling and visual separation.

**Problem:** global color-frequency aggregation then makes exactly the same prediction as connected-component extraction. The retained counterexample and the new probe show this rival fits all 5 canonical labeled pairs, so canonical agreement alone cannot reject it.

**Alternatives considered:** keep unique colors and add more shape diversity; reuse colors only in rare random cases; schedule a guaranteed repeated-color witness. More shape diversity does not distinguish the two rules. Rare random reuse leaves complete lessons ambiguous. I selected a scheduled witness.

**Decision:** in `repeated_distinct` and `repeated_tie`, reuse one color on the largest and smallest disconnected components. Component-wise output emits two separated runs for that color, while aggregation merges them into one total run.

**Probe/evidence:** `checks/final-shortcut-probe.json` verifies the hand-built counterexample and generated witness against Racket authority. Across 300 final draws, 150 refute the frequency rival.

**Failure modes/limits:** this refutes aggregation by exact color, not every possible object heuristic. Same-color components must remain separated; placement therefore reserves an eight-neighbor halo.

## D2 — Make the canonical tie-break observable

**Prior choice:** sizes were effectively distinct, and the summary allowed an incorrect “color or position” tie-break.

**Problem:** the authority sorts equal-area components by ascending color. Distinct areas hide that rule. A position-based tie-break fits 3/5 canonical labels and can survive generated lessons without explicit ties.

**Alternatives considered:** random ties; ties with random colors; scheduled ties whose color and position orders disagree. Random ties do not guarantee lesson evidence. Random colors can accidentally agree with position. I selected an adversarial assignment.

**Decision:** `unique_tie` and `repeated_tie` contain exactly one equal-area pair. For that pair, the earlier row-major component receives the larger color, so ascending-color output necessarily reverses position order.

**Probe/evidence:** focused tests compare the canonical mirror with `position_tiebreak`; the final probe reports 150/300 refuting draws. The four-profile schedule places a tie witness in every three-example window.

**Failure modes/limits:** only one tied pair is generated. More complicated multiway ties remain lawful but outside this curriculum's generated support.

## D3 — Use a deterministic four-profile semantic schedule

**Prior choice:** semantic cases were sampled without a declared schedule.

**Problem:** witness frequency does not show that each complete lesson distinguishes rivals. With three demonstrations, random independent sampling can omit a needed witness.

**Alternatives considered:** increase demonstrations; rejection-sample each assembled lesson; deterministic periodic profiles. More demonstrations cost context. Whole-lesson rejection couples the sampler to labels and is harder to audit. A four-step cycle is simple and exhaustive.

**Decision:** use `unique_distinct`, `repeated_distinct`, `unique_tie`, `repeated_tie` in sample-index order, declare `LESSON_SCHEDULE_PERIOD = 4`, and require 3 demonstrations. Every cyclic length-three window includes a repeated-color and a tie profile.

**Probe/evidence:** `checks/schedule-period-current.json` enumerates every start residue across all three bands and every query rotation: 12 lessons/48 rotations, zero ambiguity. The larger random production census covers 300 lessons/1,200 rotations.

**Failure modes/limits:** consumers must preserve at least three demonstrations. The schedule receipt fixes seed 0; although profile identity depends only on sample index, geometry and colors still vary by seed.

## D4 — Advertise only exact, pixel-observable axes

**Prior choice:** the baseline exposed many controls, including dead single-valued axes and ranges clipped differently by difficulty. Unknown keys could be silently accepted.

**Problem:** overrides were not falsifiable and generated tens of thousands of contract findings. A caller could request an advertised value and receive rejection or a different grid without a loud error.

**Alternatives considered:** repair every historical axis; mark dead axes diagnostic; reduce to the meaningful interface. The extra axes did not change the semantic curriculum and would enlarge the joint contract unnecessarily.

**Decision:** retain only `grid_h` (8..16), `grid_w` (11..18), and `scene_profile` (four enum values). All values are legal in every band. Difficulty changes weights, never legal support. `observe_overrides` recovers all three from pixels; unknown keys and non-literal scalar types fail.

**Probe/evidence:** the override gate is green and focused parameterized tests exercise every profile in every band plus range/type failures.

**Failure modes/limits:** exact axis realization is tested individually and in representative combinations, not by enumerating the entire Cartesian product of both dimensions, all profiles, bands, seeds, and shapes.

## D5 — Construct all components or fail; never drop one

**Prior choice:** placement logic could rely on bounded random attempts and accept a partial scene.

**Problem:** silent omission changes the promised semantic profile and may remove the only rival witness.

**Alternatives considered:** unbounded retry; deterministic fixed slots; finite backtracking. Unbounded retry is nondeterministic in cost. Fixed slots reduce spatial diversity. I selected finite backtracking over all legal translations, ordered by shape size.

**Decision:** generate all four connected polyominoes first, enumerate legal translations, shuffle deterministically, and backtrack with an eight-neighbor blocked halo. Raise a loud construction error if no complete layout exists.

**Probe/evidence:** 96-draw per-band focused tests assert exactly four components and deterministic replay. No placement failure occurred in the final battery, 300-draw probe, or 1,200-input lesson census.

**Failure modes/limits:** the proof is constructive only for the current size/dimension domain. Increasing object areas or shrinking grids requires retesting feasibility.

## D6 — Preserve the canonical 2-D-to-long-row relation

**Prior intermediate choice:** early repaired size profiles were lawful but sometimes produced an output row no wider than the source input.

**Problem:** all canonical pairs reshape a 2-D scene into a longer one-row strip. The defect detector classified narrower outputs as transformation drift, which could encourage a crop-like shortcut.

**Alternatives considered:** raise minimum component sizes globally; reject after generation; enumerate feasible area tuples by width and profile. Global minima reduce variety. Rejection obscures support. I selected finite enumeration.

**Decision:** choose four distinct areas or one tied profile from 1..7 only when their sum is greater than the requested input width. The maximum generated total remains within ARC's 30-cell limit.

**Probe/evidence:** the red/green logs `checks/tdd-red-transformation-drift.log` and `checks/tdd-green-transformation-drift.log` cover every width/profile. Final defect lint is green.

**Failure modes/limits:** output width is a curriculum-shape constraint, not part of the abstract task rule; `strict_canonical_like` does not reject lawful shorter-row examples.

## D7 — Keep Racket authority unchanged and add an independent Python mirror

**Prior choice:** no canonical hash pin and no executable task-local semantic contract.

**Problem:** unpinned authority can drift silently, while tests need a fast independent oracle for generated structure.

**Decision:** pin `RULE_HASH = "cbb04236ecda"`; leave the canonical Racket program untouched; implement `rule_mirror` via independent BFS; cross-check representative counterexamples and witnesses through the selected Racket rule in `shortcut_probe.py`.

**Probe/evidence:** rule smoke and authority sync are green. The probe records matching component-mirror and Racket outputs.

**Failure modes/limits:** the Python mirror is test support, not the authority. A shared bug is mitigated by the structurally different Racket implementation and fixed canonical labels, not mathematically eliminated.

## D8 — Semantic scope and stopping decision

The final semantic claim is deliberately bounded to the named color-frequency and position-tie rivals, the declared schedule, and measured samples. The 300-lesson census and exhaustive fixed-seed schedule are strong finite evidence, not universal induction. I stopped after the source-bound battery, task tests, schedule census, larger census, shortcut probe, and visible solve all agreed and no final blocker remained.
