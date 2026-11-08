# 26f02d922ca0 Generator Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use the repository battery together with test-driven development and verification-before-completion. This packet is already an isolated source-bound workspace; do not create or edit shared files outside the selected generator.

**Goal:** Replace the shortcut-prone, non-falsifiable generator contract with a deterministic curriculum that preserves the selected Racket rule, honors its declared controls exactly, emits canonical-scale examples in every difficulty band, and contains measured counterexamples to the strongest canonical shortcuts.

**Architecture:** Keep the Racket authority unchanged. Rebuild the Python generator around (1) a small connected-shape library, (2) four deterministic lesson profiles keyed by `sample_index % 4`, (3) exact `grid_h`/`grid_w` GenCtx controls, (4) task-local Python oracle/rival/witness hooks, and (5) one-cell-separated 3x3 placement slots. Keep broad executable grammar (`self_check`) separate from the empirical canonical manifold (`strict_canonical_like`).

**Tech Stack:** Python 3.12+, pytest, repository GenCtx/runtime, canonical Racket oracle and official 12-stage battery.

**Spec:** `DUTIES.md`, `ASSIGNMENT.json`, `repo/AGENTS.md`, and the canonical row for task `26f02d922ca0`.

## Global Constraints

- Preserve `GENERATOR_ID`, `TASK_ID`, and selected Racket rule hash `2ec8ce6b9b7f`.
- Edit only `repo/generators/26f02d922ca0/**` plus required packet-root review documents and check evidence.
- Reject unknown override names; declare only exact controls that can be observed in the returned grid.
- Default generation must be deterministic, global-RNG-pure, fresh-copy safe, and valid for all three difficulty bands.
- Every ordinary lesson must include at least one source-or-horizontal-mirror match and at least one non-match.
- Do not weaken the official gates or modify shared tooling to obtain a pass.

## Review Focus

- Minimum canvas (`9x12`) with four candidates must still place five separated objects without fallback or clamping.
- Explicit dimensions must be honored in every difficulty band and every schedule profile.
- Canonical-size examples must not preserve the canonical color/order shortcut while matching the canonical `(9,16,6)` profile.
- Horizontal-mirror-only candidates must be represented for asymmetric keys.
- A four-consecutive-example lesson must refute each named rival and pass `lesson_identifiable`.

---

### Task 1: Pin authority and exact override contract

**Files:**
- Modify: `repo/generators/26f02d922ca0/generator.py`
- Create: `repo/generators/26f02d922ca0/tests/test_generator_26f02d922ca0.py`

- [x] Write failing tests for `RULE_HASH`, canonical ownership, exact `grid_h`/`grid_w`, and unknown-key rejection.
- [x] Run those tests and record the expected failures against version 2.0.2.
- [x] Add `RULE_HASH`, narrow `AXES` to truthful exact dimensions, use keyed typed draws, add `observe_overrides`, and reject unknown keys.
- [x] Re-run the focused tests.

### Task 2: Build deterministic semantic curriculum

**Files:**
- Modify: `repo/generators/26f02d922ca0/generator.py`
- Test: `repo/generators/26f02d922ca0/tests/test_generator_26f02d922ca0.py`

- [x] Write failing tests for four-profile schedule coverage, mixed labels, mirror-only examples, candidate-color conflicts, candidate-order conflicts, and minimum-canvas placement.
- [x] Implement the connected 3x3 shape library, separated-slot placer, and four profile constructors.
- [x] Verify deterministic replay, fresh-copy behavior, and no mutation of Python's global random state.

### Task 3: Add semantic contract and adversarial probe

**Files:**
- Modify: `repo/generators/26f02d922ca0/generator.py`
- Create: `repo/generators/26f02d922ca0/workspace/review_probe.py`
- Test: `repo/generators/26f02d922ca0/tests/test_generator_26f02d922ca0.py`

- [x] Write failing tests for `rule_mirror`, `strict_canonical_like`, named rivals, witness-to-rival disagreement, and `lesson_identifiable`.
- [x] Implement `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, and `lesson_identifiable`.
- [x] Build a reusable probe that emits exact counterexample grids and authoritative/rival outputs as JSON.
- [x] Run the probe and retain its output under `checks/`.

### Task 4: Verify with official gates and iterate

**Files:**
- Modify as evidence requires: selected generator files only.

- [x] Run focused pytest.
- [x] Run lint, selfcheck, rule smoke, defect lint, distribution, canonical profile, semantic, diversity, override, grammar, Racket lint, and authority sync as separate source-bound stages.
- [x] Run the requested official after battery command and preserve receipts, logs, and any real remaining failures.
- [x] Compare before/after findings without claiming gates that did not complete.

### Task 5: Audit, document, and package

**Files:**
- Modify: `repo/generators/26f02d922ca0/SUMMARY.md`, `notes.md`
- Create/update: packet-root `REVIEW.md`, `DECISIONS.md`, `QUESTION_ANSWER.md`, `FEEDBACK_TO_CODEX.md`, `AUDIT.md`, `RESULTS.json`

- [x] Analyze both immutable audit targets and provide one concrete finding or a checked no-issue conclusion per exact heading.
- [x] Record exact commands, hashes, counterexamples, gate outcomes, limitations, and process friction.
- [x] Build the official deterministic compact return ZIP with `package_return.py`.
- [x] Validate archive paths, declarations, hashes, CRCs, and reproducibility from a relocated copy.

## Execution result

Implemented natively in the source-bound packet. The monolithic foreground
battery was interrupted before it emitted a complete receipt, so the documented
per-stage recovery path was used. All twelve post-change stages produced green,
source-matching receipts; exact evidence is indexed in `checks/EVIDENCE_INDEX.md`.
