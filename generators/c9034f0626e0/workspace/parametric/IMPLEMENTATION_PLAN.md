# Lattice Period Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans and superpowers:test-driven-development.

**Goal:** Build and verify a non-production period-2/period-3 parametric episode generator for task `c9034f0626e0`.

**Architecture:** `prototype.py` owns parameter validation, exact Racket materialization, lawful parent-input sampling, episode construction, rotation scoring, and evidence export. A focused pytest file fixes the public/private contract and core semantics. `README.md` documents reproduction and limits.

**Tech Stack:** Python 3.12+, standard library, pytest, included `arc_repl.isolated_verifier`, included Racket 8.10 runtime.

**Spec:** `generators/c9034f0626e0/workspace/parametric/DESIGN.md`

## Global Constraints

- Edit only task `c9034f0626e0` files and reviewer-owned return/evidence files.
- Keep canonical semantics, legal override domains, and authority unchanged; production edits are limited to strict scalar rejection and a deterministic default marker-color schedule reorder that removes a measured lesson shortcut.
- Choose `lattice_period` exactly once per episode from `{2,3}`; default `2`.
- Execute and retain labels for both programs through real Racket.
- Public challenge files omit parameters, programs, and query answers.

## Review Focus

- Boolean values must not pass integer parameter/seed validation.
- The default emitted program must equal canonical source, not merely be equivalent.
- Every retained input must distinguish periods 2 and 3.
- Every query rotation must refute the alternate period in demonstrations.
- Failed evidence construction must leave a report/manifest rather than a false pass.

---

### Task 1: Pure prototype contract

**Files:**
- Create: `generators/c9034f0626e0/workspace/parametric/prototype.py`
- Create: `generators/c9034f0626e0/tests/test_parametric_lattice_period.py`

**Interfaces:**
- Produces: `rule_source(period)`, `python_mirror(grid, period)`, `period_for_seed(seed)`, `sample_inputs(seed)`, `sample_episode(seed)`, `public_challenge(pairs, query_index=3)`, `score_rotation(predictions, chosen_period, query_index)`.

- [x] Write focused tests for exact default source, period-3 source, validation, deterministic episode-level selection, distinguishing inputs, public masking, and rotation rival elimination.
- [x] Run the tests and observe failure because `prototype.py` is absent.
- [x] Implement the minimal pure functions and parent-generator input sampling.
- [x] Run focused pure tests and obtain a pass.

### Task 2: Real-Racket evidence builder

**Files:**
- Modify: `generators/c9034f0626e0/workspace/parametric/prototype.py`
- Modify: `generators/c9034f0626e0/tests/test_parametric_lattice_period.py`

**Interfaces:**
- Produces: `run_evidence(out, base_seed, racket_path=None) -> dict` and CLI `--out`, `--base-seed`.

- [x] Add a failing integration test requiring two exact programs, Racket receipts, two masked episodes, eight rotation checks, a same-input witness, and a hash manifest.
- [x] Run it and observe the missing evidence-builder failure.
- [x] Implement isolated Racket execution, Python parity checks, export, failure reporting, and manifest hashing.
- [x] Run the complete focused suite and obtain a pass.

### Task 3: Reproduction documentation and task integration

**Files:**
- Create: `generators/c9034f0626e0/workspace/parametric/README.md`
- Modify: `generators/c9034f0626e0/notes.md`

**Interfaces:**
- Documents exact commands, parameter semantics, evidence layout, and finite limits.

- [x] Document the runnable commands and public/private separation.
- [x] Run the focused tests through the packet wrapper.
- [x] Materialize retained evidence under `WORK/checks/parametric/` and verify its report/manifest.
- [x] Run the official selected task-test stage and canonical after battery; record outcomes without changing production source.

### Task 4: Strict production call-domain repair

**Files:**
- Modify: `generators/c9034f0626e0/generator.py`
- Modify: `generators/c9034f0626e0/tests/test_generator.py`

**Interfaces:**
- Preserves every valid call and output; rejects non-literal-integer `seed` and non-literal-integer or negative `sample_index`.

- [x] Add focused failing tests for every scalar class reproduced by defect lint.
- [x] Observe 13 failures against the selected baseline.
- [x] Validate the two call arguments before schedules or RNG construction.
- [x] Run the complete selected task suite and after battery; require zero strict-scalar warnings.


### Task 5: Color-order lesson shortcut repair

**Files:**
- Modify: `generators/c9034f0626e0/generator.py`
- Modify: `generators/c9034f0626e0/tests/test_generator.py`

**Interfaces:**
- Preserves the eight legal marker colors and every exact override; default scheduling alternates marker colors below and above immutable gray-5.

- [x] Add a failing cyclic-window test requiring both `<5` and `>5` marker colors in every three-demo support under all four query rotations.
- [x] Observe failure on the grouped window `[1, 2, 3, 4]`.
- [x] Add `_MARKER_COLOR_SCHEDULE = (1, 6, 2, 7, 3, 8, 4, 9)` and keep the declared domain unchanged.
- [x] Run the focused semantic gate and complete task-local suite; require zero warnings and zero ambiguous rotations.
- [x] Run the final 12-stage after battery on the final source hash.
