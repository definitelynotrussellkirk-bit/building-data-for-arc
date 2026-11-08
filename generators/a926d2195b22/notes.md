# Working notes: `a926d2195b22`

## Final identity

- Generator version: `3.1.0`
- Generator SHA-256: `5e3b2e9674fa70056b3733e921d6197f31fe53eca4c4e1e9b08ea4a2140a6443`
- Rule hash: `eb3b09c1bddc`
- Selected rule-source SHA-256: `65c488826f479794a7a1468fad0f15576be3a144c54781fa719a7783e43f33e6`
- Selected authority file SHA-256: `2214fbb9ce2a08fb9288e2ef71aeb265bc05e20a4214287bc52d2d27ce63a385`

## Intended semantics

On a zero background, enumerate monochromatic four-connected components. Select the component with minimum cell count; when several components tie, select the one whose first cell is earliest in row-major order. Recolor only that component to 9. The selected canonical Racket program is label authority; Python mirrors are diagnostics and rival implementations.

## Repair history and decisions

1. **Baseline diagnosis.** Generator SHA `2869a082111f5a111f21eaecc83e3123645969fce4dafb4fdfd3769ecafae809` hard-coded three fixed shapes/sizes and did not truthfully realize its advertised domain. Baseline battery: 4 green, 1 advisory, 7 failed. Receipt: `checks/before/checks/a926d2195b22_before_battery_summary.json`.
2. **Version 3.0 design.** Replaced the sampler with exact-axis separated regions and random connected polyominoes. Added canonical profiles, repeated-color witnesses against `rarest_color`, tied minima against `all_minima`, strict scalar/override checks, a finite-rival lesson hook, source-bound counterexample, portable tests, and `workspace/review_probe.py`.
3. **Authority synchronization.** The selected `target_code` differed from `raw_code` only by a comment. Removed the comment; no semantic Racket change and `raw_code` remained untouched.
4. **Version 3.1 reversal.** The first large lesson census found 38 production/rotation evaluations where a generic first/topmost-object rival fit all demonstrations. The initial two-rival teaching claim was therefore withdrawn. Added executable `first_component`, a non-first-target witness, and a schedule with two non-first targets in each four-example cycle.
5. **Final probe-text correction.** After adding the third rival, the reusable probe still said “two declared executable rivals.” Added a failing regression assertion, changed the message to derive the count from `LESSON_COMPETITORS`, and reran all 185 tests.

## Distribution

- Honest axes: `grid_h=8..13`, `grid_w=8..14`, `num_objects=3..5`, `smallest_size=1..3`, `minimum_count=1..2`.
- Canonical profile cycle: `(9,10,4)`, `(10,10,3)`, `(8,12,4)`, `(9,11,3)`, `(10,12,4)`.
- Semantic profiles: `repeat_and_tie`, `repeat_only`, `tie_only`, `plain`.
- Components occupy separated construction regions and contain at most four cells.
- Foreground colors are all distinct or contain exactly one repeated color.
- Two of four examples refute `rarest_color`; two refute `all_minima`; two refute `first_component`. Every hold-one-out lesson with three demonstrations therefore contains a disagreement for every declared rival.
- Negative fixtures are explicit (`only_one_object`, `input_contains_9`, `three_way_minimum`) and cannot be mixed with ordinary axes.

## Decisive evidence

- Full final battery, required query rotations: `checks/after-v3/checks/a926d2195b22_after_battery_summary.json` — 12/12 green.
- Direct focused suite: `checks/a926d2195b22_focused_pytest_final_v2.log` — 185 passed.
- Portable staged suite: `checks/task-tests-v3/result.json` — 185 passed.
- Reusable probe: `checks/a926d2195b22_review_probe_final_v2.json` — five canonical pairs, 128 endpoint override cases, 128 rotated lesson queries, zero failures.
- Final lesson census: `checks/lesson-census-v2.summary.json` plus full `checks/lesson-census-v2.json` — 300 lessons, 1,200 unique pairs, 1,200 rotations, no declared-rival ambiguity or errors.
- Intermediate positional failure: `checks/lesson-census-v1.summary.json`; full report is retained losslessly as `checks/lesson-census-v1.json.gz` with restoration mapping in `checks/lesson-census-v1.COMPRESSION.md`.
- Strongest shortcut witness: `counterexamples/rarest_color_shortcut.json` and `checks/a926d2195b22_counterexample-v2/racket.json`.
- Final solve: `solve/summary.json`, same generator SHA, 3/3 visible examples, no rule/reference consultation during solve.

## Limitations and open questions

The lesson guarantee is only against the three declared executable rivals plus the advisory generic rivals searched by the census. It is not a proof against every imaginable program. The sampler deliberately excludes touching different-colored components, components larger than four, more than two tied minima, more than one repeated color, and object counts outside 3–5. The endpoint probe does not enumerate all interior integer values, although the final distribution and override battery sampled them independently.

Future expansion should be evidence-led: add a concrete rival, retain an exact Racket-labelled disagreement, extend the schedule so every complete lesson refutes it, and rerun both required rotations and the large census before widening the claimed domain.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `5e3b2e9674fa70056b3733e921d6197f31fe53eca4c4e1e9b08ea4a2140a6443`.

# Decisions for `a926d2195b22`

## D1 / R1 — Replace the fixed sampler rather than patch its declarations

The baseline source always placed three fixed shapes at fixed relative locations with component sizes 1, 3, and 4. Its declared surface and canonical task were broader than the distribution, so changing metadata alone would have preserved dead axes and shortcut-heavy lessons. I replaced the construction path with region-separated random polyominoes while preserving the selected Racket program as label authority.

Rejected alternatives:

- **Relabel the fixed sampler honestly.** Rejected because it would still fail to cover canonical object counts, sizes, shapes, and placements and would make poor lessons.
- **Generate arbitrary cells and reject until valid.** Rejected because it makes override exactness and runtime unpredictable. Region splitting plus bounded polyomino growth realizes valid structure without unbounded rejection.
- **Copy canonical grids into the sampler.** Rejected because it would give only five memorized layouts and no meaningful generative coverage.

## D2 / R1 — Keep only truthful, composable axes

The public axes are:

| Axis | Support | Reason |
|---|---:|---|
| `grid_h` | `8..13` | Contains canonical heights while leaving enough room for separated regions. |
| `grid_w` | `8..14` | Contains canonical widths while leaving enough room for separated regions. |
| `num_objects` | `3..5` | Covers canonical counts and fits exact separated placement in the bounded grid. |
| `smallest_size` | `1..3` | Covers the observed rule distinction without creating large, visually noisy targets. |
| `minimum_count` | `1..2` | Teaches both unique minima and the row-major tie policy. |

Each override is a strict literal integer, unknown axes fail, and every endpoint combination is exercised by the reusable probe. Negative fixtures are separated under `texture` and cannot be combined with ordinary axes. This avoids the previous pattern where an override could be accepted yet ignored or only approximately realized.

The default canonical-profile cycle is `(height, width, objects)` = `(9,10,4)`, `(10,10,3)`, `(8,12,4)`, `(9,11,3)`, `(10,12,4)`. It covers all five official input profiles without copying their layouts. Component sizes are bounded at four cells so every supported axis combination can be placed deterministically in small separated regions; this is an explicit domain limit, not a claim that larger components would violate the abstract rule.

## D3 / R1 — Preserve the canonical row-major tie behavior

The selected Racket rule sorts components by size and takes the first. On official data and the runtime object enumeration, ties resolve by row-major object order. The Python `rule_mirror` therefore ranks by `(cell_count, first_cell)` and recolors exactly one component. `all_minima` is retained as an executable rival so a lesson cannot silently teach “recolor every smallest object.”

Rejected alternative: disallow tied minima entirely. That would avoid ambiguity in generation but erase a real canonical behavior and leave learners unable to infer how ties are resolved.

## D4 / R2 — Schedule repeated-color witnesses against `rarest_color`

The globally rarest foreground color matches all five canonical labeled pairs, making it the strongest canonical-fitting shortcut found. A repeated-color profile assigns the selected minimum’s color to one larger separated component. The intended rule recolors only the minimum component; `rarest_color` recolors all cells of that color. Two of every four semantic profiles carry this witness.

The exact retained counterexample is source-bound at [`repo/generators/a926d2195b22/counterexamples/rarest_color_shortcut.json`](repo/generators/a926d2195b22/counterexamples/rarest_color_shortcut.json), and its label was checked with the selected Racket program rather than trusting only the Python mirror.

Rejected alternative: force every object to have a distinct color. That makes global color frequency numerically identical to component size and therefore reinforces the shortcut.

## D5 / R2 — Schedule tied-minimum witnesses against `all_minima`

Two of every four semantic profiles contain exactly two components at the minimum size. The target is the row-major first minimum, while the rival recolors both. This establishes a direct output disagreement instead of merely recording that a tie is present.

Rejected alternative: declare a witness that only checks `minimum_count == 2`. Presence alone is weak evidence; `WITNESS_RIVALS` now binds each witness to the executable rival it must disagree with.

## D6 / R3 — Add non-first-target witnesses after the intermediate census

The first repaired version covered repeated colors and tied minima, but the 300-lesson intermediate census found 38 evaluations where “always recolor the first/topmost component” fit all demonstrations and failed the query. I treated that as a real curriculum defect rather than a documentation-only limitation.

The final four-profile schedule deliberately places a larger component first in `repeat_and_tie` and `repeat_only`, and places a minimum first in the other two. Thus every three-of-four lesson contains at least one disagreement with `first_component`, while shapes and offsets remain randomized. `first_component` was added to `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, witness declarations, tests, and the portable probe.

Rejected alternative: merely add the rival declaration. The hook would then reject many generated lessons rather than guarantee useful lessons by construction.

## D7 / R1–R3 — Use four-example cycles with three demonstrations

Each generated lesson is assembled from four consecutive valid examples; one is held out as the query and the other three are demonstrations. The final checks rotate every one of the four positions into the query slot. The schedule supplies two repeated-color, two tied-minimum, and two non-first-target witnesses per four examples, so any three-example support set refutes all three declared rivals.

The final census sampled 100 lessons per difficulty band and checked 300 production queries plus all 1,200 hold-one-out rotations. It is strong empirical and finite-rival evidence, not exhaustive proof over all seeds or undeclared rules. No `LESSON_SCHEDULE_PERIOD` claim was added because the layout and axis cycles have multiple interacting periods; the return does not pretend the random census exhausts them.

## D8 / R1 — Keep Racket as authority and make the selected text exact

No semantic rule edit was needed. The selected `target_code` differed from the existing `raw_code` only by `;; Objects sorted by size`. I removed that comment from `target_code`; `raw_code`, behavior, and rule hash remain unchanged. This closes authority-sync drift without rewriting the canonical rule or changing any audit target.

The applied source file is `repo/shared/data/base/solutions/banks/385e738e9e70/E98__a926d2195b22.json`, final file SHA `2214fbb9ce2a08fb9288e2ef71aeb265bc05e20a4214287bc52d2d27ce63a385`.

## D9 / R1–R3 — Build a reusable future-agent probe

`workspace/review_probe.py` loads the selected generator portably and checks:

1. all five canonical pairs are accepted and match the Python diagnostic mirror;
2. the canonical-fitting `rarest_color` rival actually fits all five canonical pairs;
3. all 128 endpoint combinations of five axes across four difficulty settings realize exactly, with configurable repeated seeds; and
4. all four query rotations of generated lessons reject every currently declared executable competitor.

The probe discovers the competitor set from `LESSON_COMPETITORS`; it does not copy a rival-name list. Its final output explicitly states the remaining limits: Python is not label authority, only three declared rivals are checked, and endpoint coverage is not full interior enumeration.

## D10 — Scope and unresolved questions

The generator is intentionally a canonical-like teaching distribution, not a universal enumerator of every legal puzzle for the abstract rule. It assumes background 0, no input 9, 3–5 orthogonally separated components, component size at most four, minimum size 1–3, one or two minima, and at most one repeated foreground color. Diagonal contact is allowed because connectivity is four-neighbor.

Potential future expansion should first add a named rival and an exact witness, then widen one axis at a time. Useful candidates are larger components, two independent repeated colors, denser layouts, and more than two tied minima. Those changes were not bundled because they would enlarge the domain and lesson contract beyond the evidence needed to repair this assignment.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-92eccef38953659a:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `5e3b2e9674fa70056b3733e921d6197f31fe53eca4c4e1e9b08ea4a2140a6443`. At disposition, audited bytes match the current source.

### Current decision

Audited source repo/generators/a926d2195b22/generator.py SHA256 5e3b2e9674fa70056b3733e921d6197f31fe53eca4c4e1e9b08ea4a2140a6443. Bounded no_issue:185portable tests;128endpoint combinations,256queryrotations;64actualRacketparity inputs across4profiles/4difficultysettings. Undeclared rivals and interior override values remain uncovered. No owner execution or peer source repair. Exact evidence: `checks/audit/.a926d2195b22-task-tests.check.lock` `checks/audit/a926d2195b22-task-tests/checks/task_tests.xml` `checks/audit/a926d2195b22-task-tests/progress.log` `checks/audit/a926d2195b22-task-tests/result.json` `checks/audit/a926d2195b22/compare_parity.py` `checks/audit/a926d2195b22/parity-expected.json` `checks/audit/a926d2195b22/parity-inputs.json` `checks/audit/a926d2195b22/parity-racket.json` `checks/audit/a926d2195b22/prepare_parity.py` `checks/audit/a926d2195b22/racket-parity.json` `checks/audit/a926d2195b22/review-probe.json`

### Assessment or prior finding

## a926d2195b22

**No issue found in the bounded checks performed.** Selected generator SHA-256:
`5e3b2e9674fa70056b3733e921d6197f31fe53eca4c4e1e9b08ea4a2140a6443`.

I checked strict call/override behavior, generated component structure, the
row-major tie policy, repeated-color witnesses, non-first-target witnesses, and
three declared competitors. The portable audit task-test stage passes 185/185 at
`checks/audit/a926d2195b22-task-tests/result.json`.

The retained task probe was rerun with two seeds per endpoint and 16 lesson
starts: five canonical pairs, 128 endpoint override combinations, three
competitors, and 256 held-out query rotations all pass with no failures at
`checks/audit/a926d2195b22/review-probe.json`.

I additionally generated 64 current-source inputs spanning all four semantic
profiles and all four difficulty settings. Public canonical Racket execution
matched the generator's diagnostic mirror in all 64 cases, including tied minima
and repeated colors; see `checks/audit/a926d2195b22/racket-parity.json` and its
source-bound `parity-racket.json` receipt.

These checks do not prove the lesson unique against undeclared programs or cover
every interior override value, but I found no concrete counterexample or shortcut
beyond the limitations already documented by the generator. No source was edited.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
