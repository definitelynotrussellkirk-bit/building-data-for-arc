# ef02aedbac38 Review Implementation Plan

> **Execution:** Native in the extracted review packet; this packet intentionally has no Git metadata. TDD and retained command receipts replace commit checkpoints.

**Goal:** Add a bounded, task-local selector-role rule prototype while repairing the selected generator's strict call contract without changing any valid generated grid or canonical authority.

**Architecture:** Keep production and prototype isolated. The selected `generator.py` receives only front-door scalar validation plus focused regressions. `workspace/parametric/prototype.py` owns the proposed episode-level rule, exact Racket programs, Racket-derived labels, public/private episode separation, and evidence manifests; production remains pinned to the canonical `selector=five` rule.

**Tech stack:** Python 3.13, pytest, bundled Racket 8.10, `RacketBridge`, packet `reviewer_support` helpers.

**Spec:** `WORK/PARAMETRIC-RULES.md`, assignment `DUTIES.md`, and the unresolved audit in `evidence/review_index.json`.

## Global constraints

- Edit only `generators/ef02aedbac38/`, its task tests, and reviewer-owned `WORK/` reports/evidence.
- Preserve the exact canonical Racket program and `RULE_HASH=0e568f927b22`.
- The prototype setting is selected once per episode and never exposed in public query files.
- Every retained label, including counterfactual labels, is executed by bundled Racket.
- Valid `(seed, sample_index, difficulty, overrides)` calls must produce byte-for-byte identical grids before and after the repair.
- Reject Boolean seeds/indices, negative indices, and every difficulty outside `None|easy|medium|hard`.

## Review focus

- `bool` must not pass as an integer seed or sample index.
- Numeric difficulties `0` and `1.0` must be rejected even though Python equates some numerics with booleans.
- The alternate selector must choose companion-color cells and paint them 5, not merely recolor the canonical mask.
- Public episodes must omit parameter names, programs, metadata, and query answers.
- Canonical/default prototype text must exactly equal `program_solution`, not a normalized equivalent.

---

### Task 1: Proposed selector-role prototype

**Files:**
- Create `workspace/parametric/prototype.py`
- Create `workspace/parametric/README.md`
- Create `tests/test_parametric_selector_role.py`
- Generate evidence under `WORK/checks/parametric/selector-role-v1/`

**Interface:** `choose_setting(seed)`, `program_for(setting)`, `apply_python(grid, setting)`, `build_episode(seed, setting=None)`, `public_challenge(episode)`, and CLI `--out`.

- [x] Write focused tests for strict parameter selection, exact canonical program equality, companion program semantics, deterministic complete episodes, and public-file redaction.
- [x] Run the new tests and retain the expected RED failure because the prototype is absent.
- [x] Implement the minimal prototype with settings `five` (canonical/default) and `companion` (proposed).
- [x] Execute both exact Racket programs on all retained labels and canonical pairs; materialize two complete episodes and a shared difference witness.
- [x] Run focused tests and the evidence builder to GREEN.

### Task 2: Strict call-contract repair

**Files:**
- Modify `generator.py`
- Modify `tests/test_generator_ef02aedbac38.py`
- Add a minimal counterexample JSON if useful.

- [x] Add regression tests covering valid-call replay plus invalid seed, sample-index, and difficulty scalars.
- [x] Run task tests and retain the expected RED strict-scalar failures.
- [x] Extend `_validate_call` to validate `seed` and `sample_index`, narrow difficulty to the three named bands or `None`, and call it before `gen_ctx`.
- [x] Verify all invalid calls fail and all representative valid calls are unchanged from a pre-repair snapshot.
- [x] Run focused tests and defect lint to GREEN.

### Task 3: Full verification and handoff

- [x] Run after battery, portable task tests, and source-bound lesson census.
- [x] Complete the post-repair visible-only solve without consulting the rule during that solve.
- [x] Complete two findings-only audit targets without editing them.
- [x] Update task notes plus `REVIEW.md`, `DECISIONS.md`, `QUESTION_ANSWER.md`, `FEEDBACK_TO_CODEX.md`, and `RESULTS.json` with exact commands and limitations.
- [x] Replay final checks, self-review the patch, and build `review_response_review-c63de7bc6ec5b5ce.zip`.
