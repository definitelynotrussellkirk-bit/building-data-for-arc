# Working notes: 0d27a69b5a98

## Final source identity

- Generator version: `2.1.0`
- Generator SHA-256: `a0c84b5b70f7be5a103647787110bf05f2a6de148e3907319bdc38312f135fc7`
- Selected rule hash: `84d7043f128c`
- Racket authority changed: **no**

## Baseline diagnosis

Version `1.3.1` generated only objects on the top/left (“primary”) side and left the opposite half empty. Consequently, the canonical-fitting rival “always copy primary to secondary” explained every lesson. It also declared controls that were not literal/observable, allowed identity or undefined degenerate textures, omitted `RULE_HASH`, and could vary across Python hash seeds because it iterated an unordered side set.

The initial battery was interrupted in `rule_smoke`; its retained partial reports still exposed the missing rule pin, unprobeable axes, and override drift (`checks/before*`). The test-first repair began at 46 failures / 2 passes (`checks/task-tests-red.log`).

## Final design

The Python oracle exactly mirrors the selected Racket rule: find the unique full color-9 row or column and copy every nonzero, non-9 source cell to its in-bounds reflection, regardless of source side. Public inputs remain accepted, including clipped mirrors.

Declared controls are now only the controls that can be observed exactly:

- `grid_h`: 7..10
- `grid_w`: 8..10
- `axis_orientation`: vertical or horizontal
- `n_colors`: 1..3

Default sampling rotates through the four exact canonical height/width/orientation profiles. Constructive backtracking places nonconflicting source/mirror orbits and always leaves an output-changing witness. Generation rejects unknown or malformed overrides and is deterministic across Python hash seeds.

## Curriculum history

The first repair used a three-slot `primary, secondary, bilateral` cycle. Its ordered production census was 300/300 clean, but arbitrary query rotation held out the only bilateral example in 201/1,200 rotations (`checks/lesson-census.json`). That design was rejected.

Version `2.1.0` uses `primary, bilateral, secondary, bilateral`. With three demonstrations and one query, every consecutive three-example production window and every three-of-four query rotation contains a bilateral counterexample. The final census found:

- production: 300/300 identifiable
- rotations: 1,200/1,200 identifiable
- unique inputs: 1,197
- materialization/hook/scoring errors: 0

Evidence: `checks/final-lesson-census.json`.

## Rivals and retained witness

The declared rivals are:

1. `primary_only_copy`: only top/left cells are sources.
2. `empty_side_only_copy`: reflect only when exactly one side is empty.

The retained secondary-source counterexample is under `counterexamples/review-d279da981a00a49e-primary-only/`. The selected Racket authority mirrors the secondary-side objects, while `primary_only_copy` leaves the input unchanged. The exact Racket receipt is source-bound to the final generator hash.

## Final verification

- Full generator battery: 12/12 stages green (`checks/final-after/checks/0d27a69b5a98_after_battery_summary.json`).
- Task-local regressions: 58/58 pass (`checks/final-task-tests-58/result.json`).
- Required-rotation semantic gate: 48/48 rotations identifiable in its 12-lesson smoke sample (`checks/final-semantic-rotations/checks/0d27a69b5a98_after_semantic_gate.json`).
- Override audit: 6,120/6,120 accepted draws, zero findings/errors, unknown keys rejected (`checks/final-after/checks/0d27a69b5a98_after_override_results.json`).
- Rule smoke: 120/120 Racket applications, zero identity/OOB/mutation failures (`checks/final-after/checks/0d27a69b5a98_after_rule_smoke.json`).

## Known limits

The identifiability claims are finite and relative to the two declared rivals; they do not enumerate all possible human or program hypotheses. Generated examples keep complete mirror orbits in bounds and source objects at least one cell from the axis, while the validator and oracle also support the broader canonical rule domain, including clipped public cases. Selected canonical and task Racket sources are synchronized; one archival `raw_code` source differs textually but independently solves all public pairs, so no authority edit was made.
## Current reviewer considerations

Source SHA-256: `a0c84b5b70f7be5a103647787110bf05f2a6de148e3907319bdc38312f135fc7`.

# Decisions — 0d27a69b5a98 repair

## D1 — Pin the selected authority; do not rewrite Racket

**Decision.** Add `RULE_HASH = "84d7043f128c"` and implement an independent Python oracle for the selected canonical/task Racket source. Leave all Racket and canonical data unchanged.

**Rationale.** The selected authority is internally synchronized and solves every labeled pair. The discrepancy is in lesson generation, not rule execution. Authority-sync reports one textually divergent archival `raw_code`, but both selected sources are byte-equivalent and the archival source also has execution parity on all public pairs.

**Alternatives rejected.** Replacing the selected rule with the archival implementation would alter authority without fixing the curriculum. Editing the canonical row would be unsupported.

**Evidence.** `checks/final-after/checks/0d27a69b5a98_after_authority_sync.json`; canonical-oracle regression in `repo/generators/0d27a69b5a98/tests/test_generator.py`.

## D2 — Make the declared axis contract literal and minimal

**Decision.** Replace the nine broad/alias/degenerate controls with four observable controls: `grid_h`, `grid_w`, `axis_orientation`, and `n_colors`. Reject unknown keys and invalid types/ranges.

**Rationale.** The baseline advertised controls such as palette aliases, density, and degenerates that either did not independently control generation or produced inputs outside an output-changing teaching domain. A small exact contract is easier to audit and compose.

**Alternatives rejected.** Keeping legacy axes as ignored compatibility aliases would preserve misleading API surface. Keeping `no_line`, `no_objects`, or `already_mirrored` would teach undefined or identity behavior rather than the rule.

**Evidence.** Final override audit accepted 6,120/6,120 draws with zero findings/errors and rejected unknown keys: `checks/final-after/checks/0d27a69b5a98_after_override_results.json`.

## D3 — Treat either side as a lawful source

**Decision.** Generate three semantic profiles: `primary_only`, `secondary_only`, and `bilateral`. The oracle copies all nonzero, non-9 cells to in-bounds mirrors, matching the selected authority.

**Rationale.** Every canonical pair places source objects on the top/left side, so a one-way copy shortcut fits them all. Secondary-only examples are the smallest direct counterexample. Bilateral examples additionally disprove “mirror only when one half is empty.”

**Alternatives rejected.** Merely randomizing axis orientation does not change the directional shortcut. Randomly swapping grid halves without a declared profile makes lesson guarantees probabilistic.

**Evidence.** Retained exact Racket counterexample under `repo/generators/0d27a69b5a98/counterexamples/review-d279da981a00a49e-primary-only/`; declared rivals/witnesses in the final generator.

## D4 — Use `primary, bilateral, secondary, bilateral`, not a three-slot cycle

**Decision.** Set `EXAMPLES_NEEDED = 3` and use a four-slot schedule with the bilateral witness repeated.

**Rationale.** The first repaired schedule, `primary, secondary, bilateral`, passed all 300 ordered production lessons but failed 201/1,200 query rotations: holding out the sole bilateral pair let `empty_side_only_copy` survive. Repeating the bilateral slot guarantees every three-of-four selection contains one.

**Alternatives rejected.** Declaring lessons ordered-only would be valid but weaker than needed. Adding a fourth demonstration would increase lesson cost when a four-pair cycle already solves the rotation problem.

**Evidence.** Failed intermediate census: `checks/lesson-census.json`. Final census: `checks/final-lesson-census.json` (300/300 production, 1,200/1,200 rotations, 1,197 unique inputs).

## D5 — Keep default geometry canonical-scale; expose wider combinations only through exact overrides

**Decision.** Rotate defaults through all four canonical `(height, width, orientation)` profiles and use the canonical two-color palette size. Allow documented override combinations across heights 7–10, widths 8–10, both orientations, and one to three colors.

**Rationale.** This keeps routine lessons close to public scale while still testing composability and boundaries. It also makes profile-floor support deterministic rather than hoping random dimensions hit exact canonical profiles.

**Alternatives rejected.** A broad random rectangle distribution diluted exact-profile support. Copying canonical object geometry would risk memorization and low diversity.

**Evidence.** Profile-floor report: 60/60 exact canonical-profile hits, 20/20 in each band, `checks/final-after/checks/0d27a69b5a98_after_profile_floor.json`.

## D6 — Construct placements; do not silently drop objects

**Decision.** Enumerate legal shape/mirror placements and use deterministic backtracking. Prefer polyominoes and fall back to a singleton only when the smallest canvas requires it.

**Rationale.** The baseline retried each object independently and could finish with fewer objects than requested. Constructive placement makes every returned grid satisfy the semantic profile and preserves original source cells under the Racket row-major write semantics.

**Failure modes considered.** Mirror conflicts, axis contact, out-of-bounds reflections, occupied source mirrors, and no output-changing witness are rejected by construction/self-check.

**Evidence.** Population test across 60 indices and four difficulty settings; final self-check, grammar, diversity, and rule-smoke stages are green.

## D7 — Sort every semantically unordered traversal

**Decision.** Sort side traversal before consuming layout randomness.

**Rationale.** The first implementation iterated a Python set, so `PYTHONHASHSEED` changed RNG consumption and generated different grids. The defect linter exposed the issue; a subprocess regression failed before the fix and passes after it.

**Evidence.** `checks/hashseed-test-red.log`, `checks/hashseed-test-green.log`, and `test_generation_is_independent_of_python_hash_seed`.

## D8 — Retain executable rivals, witnesses, and a source-bound fixture

**Decision.** Declare `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, `CANONICAL_SHORTCUTS`, `SEMANTIC_WITNESSES`, and `WITNESS_RIVALS`; preserve one exact Racket disagreement fixture in the task tree.

**Rationale.** Textual claims about “variety” do not establish identifiability. Executable rivals let the semantic gate and future reviewers check whether every complete lesson—not merely the aggregate pool—contains the necessary evidence.

**Alternatives rejected.** Frequency-only witness checks can pass while individual lessons remain ambiguous. A Python-only fixture would not bind the expected output to the selected authority.

**Evidence.** Required-rotation semantic gate and final census; `checks/counterexample-apply.log`; 58/58 task tests.

## D9 — State the proof boundary explicitly

The final curriculum is checked only against the two declared plausible shortcuts, not every possible hypothesis. Generated placements keep complete mirror orbits in bounds and one cell away from the axis; the validator/oracle still accept the broader public rule domain, including clipped reflections. These are documented distribution limits, not claimed theorem-level identifiability.

## 2026-10-25 parametric reviewer build

Added a two-setting native promotion prototype without changing the production
generator or selected authority.  The default `mode=canonical` returns the exact
669-byte canonical program (SHA-256
`84d7043f128cac95c7587029ab957cb8790c12ba1434e4ec32fcdc50321ac703`).
The alternative `mode=largest_completed_color_highlight` first completes all
nonzero, non-9 cells across the full color-9 axis, then selects the unique most
frequent non-axis color in that completed intermediate and recolors it to 8.
A protected-Racket `wrong_order` witness selects the input-frequency winner
before reflection and produces a different final grid.

The adapter supports 2--6 demonstrations and 1--4 queries independently.  Its
matched input banks vary axis orientation, source side, colors, geometry and the
completed winner's original rank (2, 3 or 4).  The fourth query is a substantive
30x30 scene with 152 non-axis input cells and 186 after completion.  Bounded
self-review over seeds 0--31 covered 64 episodes / 640 labeled pairs with zero
recorded failures, six winner colors, both axis orientations and 320/320
wrong-order disagreements for the composed setting.  Staged tests passed 73/73.

Native reviewer qualification used seeds 0 and 17, three demonstrations and four
queries for both settings: 4/4 jobs qualified with 40 protected-Racket
evaluations.  Public projection verification retained 16 one-query views and
the first-turn checker passed 24 private-field invariance mutations.  Evidence
is under `checks/0d27a69b5a98/`; the source inventory is
`workspace/parametric/evidence/manifest.json`.  These are finite reviewer
results, not owner acceptance or training admission.

The pre-existing public scalar-contract audit remains explicitly unresolved;
this parametric-only addition neither edits `generator.py` nor claims to close
that finding.  The exact preservation check is
`checks/0d27a69b5a98/unresolved-audit-check.json`.

Known limits: the teaching grammar uses conflict-free complete reflection
orbits, distinct colors by role and a deliberately unique post-completion
frequency winner.  It does not prove identifiability against undeclared programs
or cover arbitrary conflicting mirror writes.
