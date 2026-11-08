# Path-Mode Prototype and Request-Contract Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair `db63430eeffa`'s portable tests and request validation, then add a task-local, Racket-verified three-setting `path_mode` prototype with three demonstrations and four distinct queries per episode.

**Architecture:** Keep the canonical production rule unchanged except for fail-closed request validation and explicit classification of its lawful square-diagonal edge texture. Put all alternate rule semantics in `workspace/parametric/prototype.py`; it samples seven inputs independently of the episode rule, executes exact Racket programs for `both`, `diagonal_first`, and `straight_first`, checks an independent Python mirror, and emits public/private evidence with opaque public IDs.

**Tech Stack:** Python 3.12+, pytest, project `reviewer_support`, `arc_repl.isolated_verifier`, bundled Racket.

**Spec:** `WORK/DUTIES.md`, `WORK/PARAMETRIC-RULES.md`, and the retained audit in `generators/db63430eeffa/evidence/review_index.json`.

## Global Constraints

- Edit only `generators/db63430eeffa/` plus required review result files under `WORK/`.
- Preserve canonical Racket authority and `RULE_HASH`; the prototype remains proposed and non-production.
- `path_mode` is chosen once per episode from `{"both", "diagonal_first", "straight_first"}`; `both` is the canonical default.
- Every retained episode has exactly 3 labeled demonstrations and 4 distinct unlabeled public queries.
- Every retained label is executed by the matching bundled-Racket program and cross-checked by an independent Python mirror.
- Public artifacts contain no hidden parameter, reference code, query answer, seed, or setting-bearing identifier.
- Unknown controls and non-literal scalar requests fail before `gen_ctx`.

## Review Focus

- Boolean, float, string, negative, and unknown request controls must fail closed.
- The lawful `square_diagonal` edge texture must remain executable while being explicitly classified.
- Every sampled unequal-gap grid must make all three path modes pairwise distinguishable.
- Rule choice must be episode-constant and independent of the input stream.
- Public challenge IDs and filenames must depend only on visible demonstrations and query inputs.

---

### Task 1: Restore portable task tests and repair request validation

**Files:**
- Modify: `generators/db63430eeffa/tests/test_generator_db63430eeffa.py`
- Modify: `generators/db63430eeffa/generator.py`

**Interfaces:**
- Produces: strict `generate(seed, sample_index, *, difficulty=None, **overrides)` request contract and a portable canonical-pair test helper.

- [ ] Replace the fixed canonical path in the existing test with `reviewer_support.find_root` and `canonical_pairs`; rerun the staged task-test check and confirm the prior path failure disappears.
- [ ] Add failing tests for invalid seed/index/difficulty values, non-literal integer overrides, unknown override names, and explicit lawful-degenerate classification.
- [ ] Run the staged task-test check and confirm the new tests fail on the current generator contract.
- [ ] Add minimal pre-`gen_ctx` validation, `VALID_DIFFICULTIES`, and `LAWFUL_DEGENERATE_TEXTURES`; bump only the generator version.
- [ ] Rerun staged task tests and the focused `defect_lint` and `override` stages.

### Task 2: Build the path-mode prototype test-first

**Files:**
- Create: `generators/db63430eeffa/tests/test_parametric_path_mode.py`
- Create: `generators/db63430eeffa/workspace/parametric/prototype.py`
- Create: `generators/db63430eeffa/workspace/parametric/README.md`

**Interfaces:**
- Produces: `rule_source(mode)`, `python_mirror(grid, mode)`, `path_mode_for_seed(seed)`, `sample_inputs(seed)`, `sample_episode(seed)`, `public_challenge(pairs)`, `score_episode(...)`, and CLI `run_evidence(...)`.

- [ ] Write tests pinning the three-value contract, exact canonical default source, fail-closed mode validation, seven distinct inputs, episode-constant sampling, pairwise mode separation, 3/4 public split, and public metadata hygiene.
- [ ] Run the prototype test file and confirm it fails because `prototype.py` is absent.
- [ ] Implement the minimal prototype functions and README command.
- [ ] Rerun the prototype tests to green.

### Task 3: Execute Racket evidence and adversarial checks

**Files:**
- Generated evidence under: `WORK/checks/parametric/db63430eeffa-path-mode-v1/`
- May modify tests/prototype only through RED→GREEN fixes.

**Interfaces:**
- Consumes: Task 2 prototype API.
- Produces: one retained episode per setting, 3 demos + 4 queries each, exact rule receipts, cross-setting witness, source/runtime hashes, and rival-refutation report.

- [ ] Run the evidence CLI through `review.py run` with the bundled Racket.
- [ ] Verify all 63 setting/input applications match the Python mirror and all six declared episode-rival comparisons are refuted by demonstrations and disagree on all four queries.
- [ ] Adversarially test sampler boundaries/invalid scalar types and public/private export leakage; add a failing regression first for any issue found.
- [ ] Rerun prototype tests and the evidence CLI after fixes.

### Task 4: Complete the two bounded supplementary tickets

**Files:**
- Modify only ticket-requested evidence/result files under `WORK/` and selected peer task evidence if the ticket explicitly requires it.

- [ ] Run `python3 review.py tickets` exactly once.
- [ ] Complete only the two drawn bounded probes, preserving blocked/unknown outcomes.
- [ ] Record structured rows and exact evidence paths in `WORK/RESULTS.json`.

### Task 5: Record findings, verify, and package

**Files:**
- Modify: `generators/db63430eeffa/notes.md`
- Create/modify: `WORK/REVIEW.md`, `WORK/FEEDBACK_TO_CODEX.md`, `WORK/RESULTS.json`

- [ ] Record the canonical repair separately from the proposed prototype, including exact limitations and strongest plausible shortcut.
- [ ] Run final focused tests/checks and inspect every result rather than inferring success.
- [ ] Record the required storage checkpoint and biggest avoidable friction mitigation.
- [ ] Run `python3 review.py package --out review_response_review-2412dcedba78daeb.zip` and inspect the delta contents.
