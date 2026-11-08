# bdd177308a5b Review Repair and Parametric Prototype Plan

> **Execution:** inline in this packet; no subagent or git worktree is available. Every code change follows a retained red/green test cycle.

**Goal:** repair the selected generator's strict API, canonical-profile support, semantic teaching contract, and selected authority binding; then build and execute a source-bound one-parameter episode prototype.

**Architecture:** keep the production generator's exact-orientation rule and placement grammar. Add validation at the public `generate` boundary, use weighted full-domain dimension draws to anchor canonical 10x10 profiles, and expose one executable orientation-insensitive rival. Keep the proposed `match_relation` episode authoring interface entirely under `workspace/parametric/`, with exact canonical Racket text as the default and a single guarded comparison transformation for the alternate setting.

**Tech stack:** Python 3, pytest, task-local `gen_ctx`, `reviewer_support`, and the bundled `RacketBridge`.

**Spec:** `WORK/DUTIES.md` as printed by `python3 review.py duties`; `PARAMETRIC-RULES.md`; canonical program source in `shared/data/canonical/puzzles.jsonl`.

## Global constraints

- Edit the selected generator, new selected-task tests, task workspace, and prescribed selected-authority `target_code` only.
- Do not modify the frozen `tests/test_generator_bdd177308a5b.py` fixture.
- Preserve archival `racket_target.raw_code` byte-for-byte.
- Keep `RULE_HASH=5b8904c8dace` bound to the canonical rule.
- Original/default parametric setting must materialize byte-for-byte canonical Racket source.
- Select one parameter once per episode; execute every retained label in Racket; public challenge must omit rule, parameter, seed, and query answer.

## Review focus

- Booleans, fractional floats, numeric strings, negative indices, and invalid difficulty values must be rejected before `gen_ctx` coercion.
- Every declared axis override value must remain available in every difficulty band after profile anchoring.
- Pinned 20-draw censuses must have at least one 10x10 exact hit per band and at least 15/60 pooled envelope hits.
- The orientation-insensitive rival must differ on generated witnesses without mutating its input.
- Both parametric settings must be demonstration-identifiable and source/hash/replay bound.

### Task 1: Production generator repair

**Files:**
- Modify: `generator.py`
- Create: `tests/test_review_repairs.py`

- [ ] Add failing tests for strict public call types, pinned profile floor, executable semantic rival, and no input mutation.
- [ ] Run the new tests and retain the expected failures.
- [ ] Add `_validate_generate_args`, weighted full-domain dimension draws, `strict_canonical_like`, and the orientation witness/rival declarations.
- [ ] Run the focused tests green and run direct regression tests that do not depend on the frozen portable-path defect.

### Task 2: Selected authority synchronization

**Files:**
- Modify through the prescribed two-step tool: the two selected `racket_target.target_code` fields only.
- Preserve: both `racket_target.raw_code` fields.

- [ ] Dry-run `arcpuzzles authority-sync ... --selected-only` into a proposal.
- [ ] Inspect exact proposed paths/hashes and apply that reviewed proposal.
- [ ] Verify exact selected authority convergence plus rule-smoke execution parity.

### Task 3: Parametric episode prototype

**Files:**
- Create: `workspace/parametric/prototype.py`
- Create: `workspace/parametric/README.md`
- Create: `tests/test_parametric_variant.py`

- [ ] Add failing tests for exact canonical default, distinct quarter-turn relation source, one-parameter complete episodes, Racket-executed labels, rival refutation, public masking, and hash-bound evidence.
- [ ] Run tests and retain the missing-module failure.
- [ ] Implement `match_relation in {exact, quarter_turn_cw}` with four authored lawful inputs containing distinct exact and quarter-turn candidates.
- [ ] Materialize two retained episodes covering both settings and run tests green.

### Task 4: Verification and handoff

- [ ] Run the required after battery and selected task-test stage; retain the inherited frozen-fixture preflight blocker separately.
- [ ] Run the 100-per-band rotated-query lesson census because a plausible rival is declared.
- [ ] Complete the exposed post-repair solve without reopening rule/generator/reference files during the solve.
- [ ] Draw and complete both adversarial audits without modifying audit targets.
- [ ] Write `REVIEW.md`, `DECISIONS.md`, concise task `notes.md`, question answer, feedback, and `RESULTS.json` with exact commands/statuses.
- [ ] Package, verify the package, and inspect its manifest before returning it.
