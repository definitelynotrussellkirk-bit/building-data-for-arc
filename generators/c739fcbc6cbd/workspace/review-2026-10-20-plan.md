# c739fcbc6cbd Repair and Parametric Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair the measured strict-scalar defect, make the strongest canonical-fitting shortcut executable and reliably refuted by generated lessons, and add a separate Racket-verified `period_factor` prototype.

**Architecture:** Keep the canonical rule and authority untouched. Add validation and finite semantic hooks to the selected generator, make the existing decoy profile a deterministic shortcut counterexample, and use a period-2 default profile schedule while preserving explicit overrides. Keep the parameterized rule in a standalone workspace prototype.

**Tech Stack:** Python 3, unittest/pytest, packet generator APIs, Racket 8.10 bridge, JSON evidence.

**Spec:** `generators/c739fcbc6cbd/workspace/review-2026-10-20-design.md`

## Global Constraints

- Edit only selected task files under `generators/c739fcbc6cbd/` plus required return/evidence files.
- Do not modify the canonical Racket source or `RULE_HASH`.
- Do not modify the frozen `test_generator_c739fcbc6cbd.py` fixture.
- Explicit `scene_profile` overrides must remain exact.
- The prototype must remain outside selected production execution.
- Every label in retained prototype evidence must be produced by the Racket bridge.

## Review Focus

- Bool/float/string call arguments must not be accepted as integers.
- A negative `sample_index` must fail before any schedule arithmetic.
- The row-major rival must fit all labeled canonical pairs and disagree on a retained generated input.
- Every period-2 lesson start and query rotation must retain a rival-refuting demonstration.
- Both prototype settings must be episode-consistent and distinguishable from each other on every retained pair.

---

### Task 1: Strict call contract

**Files:**
- Create: `generators/c739fcbc6cbd/tests/test_review_repairs.py`
- Modify: `generators/c739fcbc6cbd/generator.py`

**Interfaces:**
- Consumes: public `generate(seed, sample_index, *, difficulty=None, **overrides)`.
- Produces: literal-integer validation with nonnegative `sample_index`.

- [ ] Write tests that reject bool/float/string seeds and sample indexes and reject negative sample indexes.
- [ ] Run the focused tests and confirm they fail because invalid values are accepted.
- [ ] Add minimal validation at the top of `generate()`.
- [ ] Run the focused tests and the frozen task fixture; confirm both pass.

### Task 2: Executable shortcut and teaching schedule

**Files:**
- Modify: `generators/c739fcbc6cbd/tests/test_review_repairs.py`
- Modify: `generators/c739fcbc6cbd/generator.py`
- Create: `generators/c739fcbc6cbd/workspace/counterexamples/row_major_first_two.json`

**Interfaces:**
- Consumes: `_phase_output`, `_dots`, `generate`, canonical pairs.
- Produces: `row_major_first_two`, semantic declarations, `schedule_profile`, `LESSON_SCHEDULE_PERIOD=2`, and a deterministic decoy witness.

- [ ] Write tests proving the rival fits every canonical pair, changes a specific decoy input, every explicit decoy profile refutes it, and every four-sample default window remains identifiable under every query rotation.
- [ ] Run tests and confirm failures are due to missing rival/declarations and nondeterministic witness coverage.
- [ ] Implement the rival, witness, semantic declarations, guaranteed decoy placement, and period-2 default schedule without changing explicit overrides.
- [ ] Generate the exact counterexample JSON from real functions and verify its hashes/output grids.
- [ ] Run focused and frozen tests; confirm all pass.

### Task 3: Period-factor prototype

**Files:**
- Modify: `generators/c739fcbc6cbd/tests/test_review_repairs.py`
- Create: `generators/c739fcbc6cbd/workspace/parametric/prototype.py`
- Create: `generators/c739fcbc6cbd/workspace/parametric/README.md`
- Create: `generators/c739fcbc6cbd/workspace/parametric/rules/period_factor_2.rkt`
- Create: `generators/c739fcbc6cbd/workspace/parametric/rules/period_factor_3.rkt`

**Interfaces:**
- Produces: `ALLOWED_PERIOD_FACTORS`, `DEFAULT_PERIOD_FACTOR`, `rule_source`, `python_mirror`, `build_episode`, `run_probe`.

- [ ] Write tests for allowed/default values, episode-level parameter reuse, Python setting distinction, and public-query omission.
- [ ] Run tests and confirm failure because the prototype does not exist.
- [ ] Implement the smallest standalone prototype and README.
- [ ] Run tests to green.
- [ ] Execute the Racket probe through `review.py run`; retain generated evidence and exact rule files under the task workspace.

### Task 4: Full verification and return evidence

**Files:**
- Modify: task notes and review return files required by `DUTIES.md`.

**Interfaces:**
- Consumes: repaired generator, task tests, semantic declarations, prototype.
- Produces: completed after battery, task-test receipt, schedule census, lesson census, post-repair solve, audits, decisions, question answer, feedback, and package.

- [ ] Run the full after battery and resolve only source-backed blocking findings.
- [ ] Run selected task tests explicitly.
- [ ] Enumerate the period-2 schedule and run 100 lessons per band with query rotations.
- [ ] Complete the post-repair visible-only solve without reopening rule/reference sources during the solve lane.
- [ ] Complete both findings-only audits and all required handoff documents.
- [ ] Replay the return patch on a fresh packet copy, package with `review.py package`, and verify the produced ZIP.
