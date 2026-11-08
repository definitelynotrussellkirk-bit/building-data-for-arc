# Rotation Kaleidoscope Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair the selected rotation-kaleidoscope generator so strict checks, portable task tests, canonical-profile support, and reflection-vs-rotation lesson identifiability pass, while adding a separate Racket-verified episode-level handedness prototype.

**Architecture:** Keep the canonical Racket authority and selected production rule unchanged. Strengthen only input generation, validation, and semantic declarations in `generator.py`; keep the proposed rule parameter under `workspace/parametric/`. Use portable `reviewer_support` APIs in task tests and retain exact check evidence under `WORK/checks/`.

**Tech Stack:** Python 3.12+, pytest/unittest-compatible task tests, ARCpuzzles generator runtime, bundled Racket 8.10 bridge.

**Spec:** `WORK/DUTIES.md`, `WORK/PARAMETRIC-RULES.md`, unresolved audit in `generators/196a7ec58bbc/evidence/review_index.json`.

## Global Constraints

- Do not edit the canonical Racket rule or its `RULE_HASH` (`24bc23963715`).
- Edit only selected-task files plus reviewer handoff files and check evidence.
- Canonical 2×2 diagonal inputs remain accepted as an answer-equivalent exception.
- Production generation must return only inputs with four distinct rotations and a concrete rotation-vs-reflection witness.
- The parametric extension is a proposed task-local prototype, never the selected production path.
- Exact hidden prototype parameters are selected once per complete episode.
- No Git metadata is present in the packet, so commit steps are inapplicable.

## Review Focus

- Boolean, float, string, and negative `sample_index` values must fail before `gen_ctx` accepts/coerces them.
- Easy-band 20-draw support must include at least one canonical `(2×2, 2-color)` profile without admitting ambiguous 2:2 color layouts.
- A transpose-symmetric demonstration set must be rejected when mirror tiling survives all demonstrations and changes the query.
- Every ordinary generated input must distinguish canonical rotation tiling from reflection tiling.
- Portable task tests must resolve canonical data from both the library layout and isolated staged runtime.

---

### Task 1: Make the task test suite portable and add red contract tests

**Files:**
- Modify: `generators/196a7ec58bbc/tests/test_generator_196a7ec58bbc.py`

**Interfaces:**
- Consumes: `reviewer_support.find_root`, `canonical_pairs`, `canonical_path`.
- Produces: failing behavioral tests for production repair and prototype interfaces.

- [ ] Replace fixed-depth canonical paths with `reviewer_support` helpers and verify the existing suite reaches pytest in the staged runtime.
- [ ] Add a test that invalid `seed`/`sample_index` scalar types and negative indices raise `ValueError`.
- [ ] Add a test that explicit `(grid_n=2, palette_size=2)` draws are lawful, have 3:1 color counts, and have four rotations.
- [ ] Add a 20-draw-per-band profile test requiring at least one canonical profile in each band.
- [ ] Add semantic tests for `rule_mirror`, the named reflection rival, witness declarations, the retained seed-33 ambiguity, and generated identifiable lesson windows.
- [ ] Add prototype tests for canonical default, alternate handedness, episode-level parameter stability, public answer masking, and distinct outputs.
- [ ] Run staged task tests and confirm they fail for missing production/prototype behavior rather than import/path errors.

### Task 2: Repair generator validation, distribution, and semantic teaching contract

**Files:**
- Modify: `generators/196a7ec58bbc/generator.py`

**Interfaces:**
- Produces: `rule_mirror(grid)`, `strict_canonical_like(grid)`, `lesson_identifiable(demos, query)`, `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`.

- [ ] Add exact-integer validation for `seed` and nonnegative `sample_index` at the start of `generate`.
- [ ] Permit 2-color 2×2 generated inputs, using 3:1 counts so four rotations are possible; keep the canonical 2:2 diagonal exception accepted only by `self_check`.
- [ ] Add a deterministic easy-band profile anchor so the first 20 draws contain 2×2 two-color cases; preserve exact override behavior.
- [ ] Implement independent canonical rotation tiling and reflection-tiling rival functions.
- [ ] Require ordinary generated grids to distinguish rotation from reflection in both randomized and fallback paths.
- [ ] Declare the semantic witness/rival and a lesson hook that rejects any lesson where the rival fits all demonstrations and changes the query.
- [ ] Run task tests until green, then run focused lint, defect lint, profile floor, semantic gate, and override stages.

### Task 3: Build a separate Racket-verified handedness prototype

**Files:**
- Create: `generators/196a7ec58bbc/workspace/parametric/prototype.py`
- Create: `generators/196a7ec58bbc/workspace/parametric/verify.py`
- Create: `generators/196a7ec58bbc/workspace/parametric/README.md`
- Generated by verifier: `workspace/parametric/programs/*.rkt`, `episodes/*.json`, `evidence/manifest.json`

**Interfaces:**
- Produces: `program_for(handedness)`, `solve(grid, handedness=...)`, `generate_episode(seed, handedness=None)`, `public_challenge(episode)`.

- [ ] Define bounded `handedness ∈ {clockwise, counterclockwise}` with canonical/default `clockwise`.
- [ ] Keep TL=original and BR=180° invariant; swap CW/CCW between TR and BL for the alternate setting.
- [ ] Select handedness once per episode and generate three demonstrations plus one query whose inputs distinguish both settings.
- [ ] Materialize exact Racket for both settings and execute all stored labels through `RacketBridge`.
- [ ] Check that every demonstration and query refutes the alternate setting, write masked public challenges, and retain hashes/commands/limitations.
- [ ] Run prototype-focused task tests and the standalone verifier.

### Task 4: Full verification and reviewer handoff

**Files:**
- Modify: `generators/196a7ec58bbc/notes.md`
- Create/modify: `WORK/REVIEW.md`, `WORK/DECISIONS.md`, `WORK/QUESTION_ANSWER.md`, `WORK/FEEDBACK_TO_CODEX.md`, `WORK/RESULTS.json`
- Create minimal retained counterexample evidence under `generators/196a7ec58bbc/counterexamples/` if needed.

- [ ] Run the required after battery and staged task tests, retaining any failed attempts honestly.
- [ ] Run a 100-per-band rotated-query lesson census and inspect declared-rival results.
- [ ] Complete the visible-only post-repair solve without consulting the Racket rule during that solve.
- [ ] Draw and complete both findings-only audits, with reproducible evidence for any issue.
- [ ] Record exact commands, working directories, exits, source hashes, limitations, and the `qwen9-data-value` answer.
- [ ] Replay the patch/final source checks required by `RETURN-GUIDE.md` and package only `review_response_review-1e5bbd7c27fe6e1c.zip`.
