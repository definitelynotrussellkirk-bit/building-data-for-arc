# Strict Request Contract and Parametric Cycle Direction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the current defect-lint failures without changing the canonical rule, and add an isolated Racket-backed episode-level `cycle_direction = next | previous` prototype that preserves the original three-region reasoning family.

**Architecture:** The selected generator remains the canonical `next`-direction execution path. A strict request validator rejects coercible scalar aliases before `GenCtx` construction, while a sparse scheduled connected-mask profile gives the ordinary distribution measured overlap with canonical singleton-marker structure without narrowing the grammar. A separate `workspace/parametric/` module materializes complete next/previous episodes and obtains every retained label by executing the exact setting-specific Racket program.

**Tech Stack:** Python 3.12, pytest, task-local `reviewer_support`, `review_diagnostics.structural_signature`, `arc_repl.racket_bridge.RacketBridge`, canonical Racket DSL.

**Spec:** `../../../../DUTIES.md`; `../../../../PARAMETRIC-RULES.md`; canonical task `shared/data/canonical/puzzles.jsonl` task ID `19e04051ad0d`.

## Global Constraints

- Edit only `repo/generators/19e04051ad0d/` and reviewer-owned handoff/evidence paths.
- Do not edit the frozen `tests/test_generator_19e04051ad0d.py` fixture.
- Keep the canonical Racket source and `RULE_HASH = "3448ae999e2e"` unchanged.
- Preserve `next` as the selected generator and canonical parametric default.
- Choose the proposed parameter once per complete episode, never per pair.
- Retained parametric outputs must be exact Racket executions, not Python-only labels.
- The packet has no Git repository; replace commit steps with source-hash and check receipts.

## Review Focus

- Boolean, float, and string aliases for `seed`, `sample_index`, `difficulty`, and `bg_color` must be rejected before generation; Task 1 pins each class.
- Valid boundary overrides and `None`-means-no-override must still round-trip exactly; Task 1 pins both.
- The canonical singleton-marker support `{0, 10, 18}` must overlap ordinary generated support in every band without forcing all masks connected; Task 2 pins overlap and retained random-profile diversity.
- Every parametric episode must use one immutable setting and demonstrations/query must distinguish the rival setting; Task 3 pins both.
- Exact `next` and `previous` Racket programs must match an independent Python mirror and public challenges must hide setting, program, and query answer; Task 3 pins all four boundaries.

---

### Task 1: Strict request validation

**Files:**
- Create: `tests/test_strict_request_contract.py`
- Modify: `generator.py`

**Interfaces:**
- Consumes: existing `generate(seed, sample_index, *, difficulty=None, **overrides)` and `AXES`.
- Produces: `_validate_request(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None`; strict `bg_color` draw behavior.

- [ ] **Step 1: Write failing scalar-contract tests**

Create table-driven tests proving that booleans/floats/strings for integer or color fields, negative `sample_index`, and unsupported difficulties raise `TypeError` or `ValueError`; include a literal `bg_color=9.75` regression.

- [ ] **Step 2: Run the focused test and verify RED**

Run: `pytest -q generators/19e04051ad0d/tests/test_strict_request_contract.py`
Expected: failures showing the current generator accepts invalid scalars.

- [ ] **Step 3: Implement `_validate_request` and strict color draw**

Validate exact Python types, nonnegative sample index, the four supported difficulty values, known override names, and per-axis override types. Call it before `gen_ctx`; use `ctx.draw_color_strict("bg_color")` as defense in depth. Preserve `None` as the existing no-override convention.

- [ ] **Step 4: Run focused and existing task tests**

Run the focused file, then all `generators/19e04051ad0d/tests/`; expected PASS.

- [ ] **Step 5: Record source hash and test receipt**

Write the command, exit code, and post-change generator SHA-256 into reviewer evidence/`RESULTS.json`; no Git commit is available in this packet.

### Task 2: Canonical structural-support profile

**Files:**
- Create: `tests/test_canonical_structural_support.py`
- Modify: `generator.py`

**Interfaces:**
- Consumes: existing `_place_region`, keyed RNGs, and `review_diagnostics.structural_signature`.
- Produces: a deterministic scheduled connected-foreground mask profile within ordinary generation; random masks remain the majority profile.

- [ ] **Step 1: Write failing structural-support tests**

Assert that each difficulty band’s linter sampling window (`seed == sample_index` for 1..8) intersects canonical `persistent_markers` support, and that a wider sample contains both zero-marker connected profiles and positive-marker random profiles.

- [ ] **Step 2: Run the focused test and verify RED**

Run: `pytest -q generators/19e04051ad0d/tests/test_canonical_structural_support.py`
Expected: canonical-support intersection assertion fails on the current source.

- [ ] **Step 3: Add the minimal connected-mask profile**

For a sparse, explicit sample-index schedule, seed each region with one horizontal connected row spanning all its columns, then grow a keyed random 4-connected foreground until the existing target solid count is reached. Keep current random mask generation for all other indices and retain the same hole fractions, layouts, colors, separators, and self-check contract.

- [ ] **Step 4: Run focused tests and the defect linter**

Run the new test, all task tests, and the defect-lint stage. Expected: tests PASS and both `persistent_markers` and strict-scalar warnings disappear.

- [ ] **Step 5: Record source hash and detector receipt**

Retain the before/after support sets and exact source hash; no Git commit is available.

### Task 3: Isolated cycle-direction prototype

**Files:**
- Create: `workspace/parametric/prototype.py`
- Create: `workspace/parametric/README.md`
- Create: `tests/test_parametric_cycle_direction.py`
- Create evidence: `WORK/checks/parametric/evidence.json` and public challenge JSON files.

**Interfaces:**
- Consumes: lawful inputs from the selected generator, canonical Racket rule text, and `RacketBridge`.
- Produces: `ALLOWED_DIRECTIONS = ("next", "previous")`, `DEFAULT_DIRECTION = "next"`, `choose_direction`, `program_for`, `apply_python`, `apply_racket`, `build_episode`, `parameter_rival_findings`, and `materialize`.

- [ ] **Step 1: Write failing prototype contract tests**

Pin canonical default, next/previous output divergence, one setting per complete 3-demo-plus-query episode, rival rejection, exact Racket/Python parity for both settings, and public challenge secrecy.

- [ ] **Step 2: Run the focused test and verify RED**

Run: `pytest -q generators/19e04051ad0d/tests/test_parametric_cycle_direction.py`
Expected: failure because the prototype file does not exist.

- [ ] **Step 3: Implement the minimal isolated prototype**

Use deterministic selected-generator inputs, materialize `(remainder (+ i 1) n)` for `next` and `(remainder (+ i (- n 1)) n)` for `previous`, validate exact scalar types/settings, and keep the setting immutable across each episode.

- [ ] **Step 4: Verify Racket parity and materialize evidence**

Run the focused test, then execute the prototype through `review.py run` into `WORK/checks/parametric/`. Expected: two complete episodes, no rival findings, distinct outputs, Racket-derived labels, and public JSON with no parameter/program/query output.

- [ ] **Step 5: Document scope and limitations**

State that this is a separate proposal, does not change selected execution or approval, covers only the declared two-value parameter, and preserves the original task’s object roles and reasoning.

### Task 4: End-to-end verification and handoff

**Files:**
- Modify: `notes.md`
- Create/update reviewer-owned: `WORK/REVIEW.md`, `WORK/DECISIONS.md`, `WORK/QUESTION_ANSWER.md`, `WORK/FEEDBACK_TO_CODEX.md`, `WORK/RESULTS.json`, `WORK/AUDIT.md`, `WORK/solve/`.

**Interfaces:**
- Consumes: final source/tests/prototype and all retained receipts.
- Produces: a replayable `review_response_review-12bfd50e9b774ba3.zip`.

- [ ] **Step 1: Run selected task tests and the complete after battery**

Use the packet wrappers and fresh output paths; retain every failure and iterate only from reproduced causes.

- [ ] **Step 2: Run the required lesson census and post-repair visible solve**

Use 100 lessons per band with query rotation, then solve the exposed visible task without consulting its hidden answer during the solve; declare prior exposure honestly.

- [ ] **Step 3: Run the two assigned findings-only audits once**

Reproduce or clear each target under its exact `## TASK_ID` heading without editing audit-source generators.

- [ ] **Step 4: Complete concise reports and package**

Record exact commands, working directories, exit codes, source hashes, remaining failures, acceptance status, and prototype limitations; run `review.py package`.

- [ ] **Step 5: Replay the final patch in a fresh extraction and rerun focused tests**

Confirm every changed path and final generator hash, then retain the replay receipt before claiming completion.
