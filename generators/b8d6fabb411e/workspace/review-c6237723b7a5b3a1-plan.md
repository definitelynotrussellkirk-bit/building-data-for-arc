# Alignment-Scope Parametric Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a source-bound, runnable, unapproved episode-level `alignment_scope` prototype for `b8d6fabb411e` while leaving the selected canonical generator and Racket authority unchanged.

**Architecture:** The canonical/default `span` setting is the exact selected Racket program. The proposed `boundary` setting changes only the row/column membership predicates so markers fire on square boundary rows/columns, not interior span rows/columns. Inputs come from the selected generator with side-3/4 squares and guaranteed interior-aligned markers; one hidden setting is chosen once per episode, all labels are executed by the bundled Racket bridge, and public challenges omit the hidden setting and query answer.

**Tech Stack:** Python 3.12, pytest, existing `reviewer_support`, existing `arc_repl.racket_bridge`, bundled Racket 8.10.

**Spec:** `../../../../PARAMETRIC-RULES.md` and assignment `review-c6237723b7a5b3a1`.

## Global Constraints

- Preserve `generator.py`, canonical `RULE_HASH=e88f12aefcff`, and approval state.
- Put prototype code under `generators/b8d6fabb411e/workspace/parametric/` and focused tests under `generators/b8d6fabb411e/tests/`.
- Default setting must be byte-identical to the selected canonical Racket program.
- Choose the hidden rule once per episode; demonstrations must refute the alternative before the query.
- Retained labels must come from actual Racket execution; public files must omit hidden parameters, source, seed, and query output.
- Evidence claims are finite and prototype-only.

## Review Focus

- Canonical program drift: fail loudly if the two row-span or two column-span edit sites no longer match exactly.
- Non-separating lessons: reject any episode whose demonstrations do not distinguish `span` from `boundary`.
- Input-domain drift: every fixture must pass the selected generator's `self_check` and contain a true interior-aligned marker.
- Hidden-data leakage: public challenges must omit parameter name/value, seed, Racket text/hash, rival metadata, and query answer.
- Invalid API values: booleans, negative seeds, and unknown settings must fail instead of coercing.

---

### Task 1: Pin the prototype contract with failing tests

**Files:**
- Create: `generators/b8d6fabb411e/tests/test_parametric_alignment_scope.py`
- Create later: `generators/b8d6fabb411e/workspace/parametric/prototype.py`

**Interfaces:**
- Produces expectations for `choose_parameters`, `canonical_program`, `render_program`, `fixture_inputs`, `python_reference`, and `public_challenge`.

- [ ] Write tests for deterministic episode-level choice, exact canonical default, guarded boundary rewrite, lawful separating fixtures, and public redaction.
- [ ] Run the focused test and verify collection/import fails because `prototype.py` does not exist.

### Task 2: Implement the minimal source-bound prototype

**Files:**
- Create: `generators/b8d6fabb411e/workspace/parametric/prototype.py`

**Interfaces:**
- Produces `choose_parameters(seed: int) -> dict[str, str]`.
- Produces `render_program(alignment_scope: str, root=None) -> str` with settings `span|boundary`.
- Produces `fixture_inputs(seed: int, root=None) -> list[Grid]` and `python_reference(grid, alignment_scope, root=None) -> Grid`.
- Produces `build_episode(seed, bridge, root=None) -> dict` and `public_challenge(episode) -> dict`.
- CLI `prototype.py --seed N --out NEW_DIR` materializes both settings and a report.

- [ ] Implement strict validators and canonical-source loading with exact site-count guards.
- [ ] Implement setting-independent fixtures from explicit `large_16x18` layouts and all four scene profiles.
- [ ] Implement Racket execution, both-setting comparison, default canonical-pair parity, public/private materialization, hashes, and finite-limit report.
- [ ] Run focused tests until green.

### Task 3: Materialize and independently verify retained evidence

**Files:**
- Create via CLI under `WORK/checks/parametric/alignment-scope-v1/`.

- [ ] Run the prototype through `WORK/run_with_racket.py` into a fresh evidence directory.
- [ ] Verify the report covers both settings, all canonical labeled pairs under `span`, Racket/Python parity, and at least one refuting demonstration per episode.
- [ ] Re-run from a second fresh output path and compare deterministic semantic hashes (excluding command/output paths).

### Task 4: Document scope and integrate task-local checks

**Files:**
- Create: `generators/b8d6fabb411e/workspace/parametric/README.md`
- Modify: `generators/b8d6fabb411e/notes.md`
- Modify: `WORK/REVIEW.md`, `WORK/DECISIONS.md`, `WORK/QUESTION_ANSWER.md`, `WORK/FEEDBACK_TO_CODEX.md`, `WORK/RESULTS.json`

- [ ] Document parameter values, default, dependent input constraints, exact command, public/private split, evidence, and limitations.
- [ ] Record strongest canonical shortcut and an exact generated disagreement witness.
- [ ] Run task-tests stage, after battery, lesson census, post-repair visible-only solve, two audits, and final patch replay/package checks.

## Execution ruling

The initial constraint to preserve `generator.py` was superseded by measured
baseline evidence: strict defect lint found 33 invalid scalar calls accepted by
the production API. The implemented exception is limited to task-local call
validation and leaves every lawful generated grid, schedule, version, and rule
byte unchanged. Red-green evidence and the final 12/12 battery are cited in the
return reports.
