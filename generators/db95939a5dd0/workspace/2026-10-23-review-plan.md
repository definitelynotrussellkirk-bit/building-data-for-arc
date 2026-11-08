# db95939a5dd0 Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:executing-plans` to implement this plan task-by-task. Every production change follows red-green-refactor.

**Goal:** Repair the selected canonical generator's API, fixture metadata, and teaching contract without changing its canonical rule; synchronize selected authority text; and add a runnable isolated shift-distance prototype.

**Architecture:** Keep `generator.py` as the only selected production implementation. Add strict validation before `gen_ctx`, derive prior eligibility from recognized non-`None` overrides, declare lawful fixtures, and make opposite-role color reuse a deterministic three-index lesson-schedule witness. Declare one executable semantic rival and use the shared hook/rival interface. Keep the proposed parameterized rule entirely under `workspace/parametric/`, with Racket bridge verification and public/private evidence separation.

**Tech Stack:** Python 3.13, pytest, existing `puzzle_generators` runtime, `reviewer_support`, bundled `arc_repl.racket_bridge`, Racket DSL.

**Spec:** `START-HERE.md`, `WORK/PARAMETRIC-RULES.md`, assignment `review-7526edee32950438`, and unresolved findings in `generators/db95939a5dd0/evidence/review_index.json`.

## Global Constraints

- Preserve `RULE_HASH = "a742202e03fb"` and canonical per-compound top-left/bottom-right shift semantics.
- Edit only selected-task paths plus the assignment-authorized selected base authority records.
- Unknown overrides fail closed; explicit `None` is omission-equivalent.
- Strict scalar validation rejects bool/float/string call arguments and out-of-range values before RNG/context construction.
- All three diagnostic textures remain lawful, self-check-clean fixtures.
- Three ordered demonstrations must refute `one_direction_per_color`; query rotations are measured separately and reported honestly.
- The parametric extension is proposed prototype evidence, never selected production authority.

## Review Focus

- Unknown-key and explicit-`None` calls must not silently change the prior.
- Validation must reject bool-as-int, negative sample indices, invalid difficulty, and every invalid declared-axis type/range.
- Schedule forcing must not override explicit controls or reduce canonical profile support below the required floor.
- A reused color must appear once as a lower region and once as an upper region in each three-index default lesson window.
- Prototype programs must be executed in Racket, keep one setting fixed per episode, and hide parameters/query labels in public challenges.

---

### Task 1: Contract and fixture repair

**Files:**
- Modify: `generators/db95939a5dd0/generator.py`
- Create: `generators/db95939a5dd0/tests/test_generator_db95939a5dd0.py`

**Interfaces:**
- Produces `_validate_call(seed, sample_index, difficulty, overrides) -> dict`, returning active non-`None` overrides.
- Preserves `generate(...)`, `self_check(...)`, `observe_overrides(...)`, and `_rule_output(...)` public behavior for valid calls.

- [ ] Write focused tests for unknown keys, omission equivalence, strict call/axis scalars, lawful fixture declarations, canonical parity, determinism, and fresh returns.
- [ ] Run the tests against version 3.1.0 and retain the expected failures.
- [ ] Add strict validation before `gen_ctx`, use active overrides for prior eligibility, and declare `LAWFUL_DEGENERATE_TEXTURES`.
- [ ] Expand `observe_overrides` only where exact values are directly observable; retain the current semantic observation contract otherwise.
- [ ] Run focused tests and the linter/override stages until green.

### Task 2: Teaching rival and deterministic witness schedule

**Files:**
- Modify: `generators/db95939a5dd0/generator.py`
- Modify: `generators/db95939a5dd0/tests/test_generator_db95939a5dd0.py`
- Create: `generators/db95939a5dd0/workspace/lesson_probe.py`

**Interfaces:**
- Produces `_one_direction_per_color(grid) -> grid` as a pure deterministic rival.
- Produces `_has_opposite_role_color_reuse(grid) -> bool`.
- Declares `EXAMPLES_NEEDED = 3`, `LESSON_SCHEDULE_PERIOD = 3`, `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, `CANONICAL_SHORTCUTS`, `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, and `lesson_identifiable(demos, query) -> list[str]`.

- [ ] Write failing tests reproducing the retained seed-2 ambiguity and requiring every three-index default window to contain a rival-refuting witness.
- [ ] Verify failures on the current source.
- [ ] Implement the rival/witness and a default-only period-three schedule that forces the canonical shared-color archetype at one residue.
- [ ] Change generalized shared-color draws to opposite-role reuse; do not alter explicit override semantics.
- [ ] Run focused tests, semantic gate with required rotations, and a 100-per-band rotating census; retain counterexamples if any.

### Task 3: Selected authority exact-text synchronization

**Files:**
- Modify only assignment-authorized records under `shared/data/base/solutions/...` selected for task `db95939a5dd0`.
- Create evidence under `../checks/authority-sync/`.

**Interfaces:**
- Canonical `program_solution` remains source; only selected `racket_target.target_code` exact text changes; archival `raw_code` remains unchanged.

- [ ] Generate a hash-bound `authority-sync --selected-only` proposal and inspect that token sequences are identical.
- [ ] Apply the reviewed proposal explicitly, copy the receipt into checks, and remove transient recovery state outside return scope.
- [ ] Run `authority_sync` and `rule_smoke` stages and verify both pass with unchanged `RULE_HASH`.

### Task 4: Isolated shift-distance parametric prototype

**Files:**
- Create: `generators/db95939a5dd0/workspace/parametric/README.md`
- Create: `generators/db95939a5dd0/workspace/parametric/prototype.py`
- Create: `generators/db95939a5dd0/workspace/parametric/rules/shift_distance_1.rkt`
- Create: `generators/db95939a5dd0/workspace/parametric/rules/shift_distance_2.rkt`
- Create: `generators/db95939a5dd0/tests/test_parametric_prototype.py`

**Interfaces:**
- `ALLOWED_SHIFT_DISTANCES = (1, 2)` and `DEFAULT_SHIFT_DISTANCE = 1`.
- `program_for(distance)`, `apply_python(grid, distance)`, `build_episode(seed, distance=None)`, `parameter_rival_findings(episode)`, `public_challenge(episode)`, and CLI evidence writer.

- [ ] Write failing tests for validation, one-setting-per-episode selection, canonical default parity, rival distinction, and public redaction.
- [ ] Implement a lawful input builder with two-cell horizontal clearance and complete three-demo/one-query episodes.
- [ ] Materialize both exact Racket programs, execute every retained label through the bundled bridge, and compare to the independent Python mirror.
- [ ] Retain a discriminating witness, one complete episode per setting, source/program hashes, private evidence, and public challenges under `checks/parametric/`.

### Task 5: Final evidence, solves, audits, and handoff

**Files:**
- Modify: `generators/db95939a5dd0/notes.md`, `generators/db95939a5dd0/SUMMARY.md`
- Create/modify: `../REVIEW.md`, `../DECISIONS.md`, `../QUESTION_ANSWER.md`, `../FEEDBACK_TO_CODEX.md`, `../RESULTS.json`, `../AUDIT.md`

- [ ] Run selected task tests and the complete after battery; preserve exact commands, hashes, failures, and counts.
- [ ] Perform the required exposed post-repair visible-only solve without reopening generator/rule/reference sources during the solve lane.
- [ ] Draw and complete both findings-only audits with source-bound reproductions or explicit clean checks.
- [ ] Answer `qwen9-data-value` with one concrete new gate, reproducible failure, false-positive risk, and cheapest test.
- [ ] Self-review for new shortcuts/distribution restriction, package the delta, replay it against a fresh extraction, rerun focused tests there, and package the final verified ZIP.
