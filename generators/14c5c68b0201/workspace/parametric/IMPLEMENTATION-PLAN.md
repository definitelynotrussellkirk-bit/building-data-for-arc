# Tiling-Axes Parametric Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Build a task-local, unapproved prototype that keeps the canonical stamp-tiling rule as `tiling_axes="both"` and adds nearby `horizontal` and `vertical` episode-wide settings, with four distinct Racket-labeled queries per setting.

**Architecture:** Leave `generator.py`, the canonical ledger, and approval metadata unchanged. A standalone `workspace/parametric/prototype.py` hash-pins the selected canonical Racket source, materializes exactly three rules by replacing one guarded paint predicate, generates deterministic lawful inputs through the selected generator, labels and analyzes every pair with the included Racket bridge, projects answer-masked public challenges, and writes source-bound evidence. Focused tests live beside the task's existing tests.

**Tech Stack:** Python 3.12, pytest, the repository's `RacketBridge`, selected generator API, and `reviewer_support` public projection/hash helpers.

**Spec:** Packet `WORK/PARAMETRIC-RULES.md` and `WORK/ARC-DESIGN.md`; assignment `review-61a29a5db5626772`.

## Global Constraints

- Edit only `generators/14c5c68b0201/` plus packet-owned reports/evidence.
- Preserve the exact canonical rule and selected generator behavior; no production parametric API or approval change.
- Parameter is chosen once per episode and fixed across demonstrations and queries.
- Default/original setting is `both`; allowed values are exactly `both`, `horizontal`, `vertical`.
- Expose demo and query counts separately; default to 3 demonstrations and 4 distinct queries.
- All retained labels and declared-setting rival predictions are executed by matching exact Racket programs.
- Public challenge names depend only on visible demonstrations and query inputs; public files omit settings, seeds, programs, and query answers.

## Review Focus

- A replacement site that no longer uniquely identifies the canonical paint predicate must fail closed.
- Boolean or non-integer seeds/counts must be rejected rather than treated as integers.
- Inputs must be lawful, unique, and make all three settings produce different labels.
- Every non-selected setting must be refuted by demonstrations before any query depends on the distinction.
- Evidence verification must detect public/private projection or file-hash tampering.

---

### Task 1: Rule contract and exact Racket materialization

**Files:**
- Create: `generators/14c5c68b0201/tests/test_parametric_tiling_axes.py`
- Create: `generators/14c5c68b0201/workspace/parametric/prototype.py`

**Interfaces:**
- Produces: `canonical_rule(root=None) -> str`, `instantiate_rule(tiling_axes="both", root=None) -> str`, `restore_canonical(program, root=None) -> str`, `evaluate(bridge, program, grid) -> grid`, constants `TILING_AXES`, `DEFAULT_TILING_AXES`, and pinned canonical SHA-256.

- [x] Write tests asserting the exact canonical hash, unchanged default source, distinct alternative sources, reversible guarded substitutions, invalid settings rejected, and canonical Racket parity on every labeled canonical pair.
- [x] Run the focused tests and confirm failure because the prototype does not exist.
- [x] Implement the minimal hash-pinned materializer and Racket evaluator.
- [x] Run the focused tests and confirm they pass.

### Task 2: Deterministic episodes, rivals, and public privacy

**Files:**
- Modify: `generators/14c5c68b0201/tests/test_parametric_tiling_axes.py`
- Modify: `generators/14c5c68b0201/workspace/parametric/prototype.py`

**Interfaces:**
- Produces: `generate_inputs(seed, demo_count=3, query_count=4)`, `choose_tiling_axes(seed)`, `make_episode(bridge, seed, tiling_axes=None, demo_count=3, query_count=4)`, `analyze_episode(bridge, episode)`, `public_challenge(episode)`, and `public_filename(episode)`.

- [x] Add tests for count/seed validation, deterministic unique lawful inputs, identical inputs across settings, three complete 3+4 episodes, Racket-derived labels, demonstration-only rival refutation, and opaque public projection/name invariance under private mutations.
- [x] Run new tests and confirm expected missing-interface failures.
- [x] Implement deterministic input scheduling, episode construction, rival analysis, and public projection.
- [x] Run the focused tests and confirm they pass.

### Task 3: Evidence writer, retained documentation, and scoped verification

**Files:**
- Modify: `generators/14c5c68b0201/tests/test_parametric_tiling_axes.py`
- Modify: `generators/14c5c68b0201/workspace/parametric/prototype.py`
- Create: `generators/14c5c68b0201/workspace/parametric/README.md`
- Modify: `generators/14c5c68b0201/notes.md`
- Create: `WORK/REVIEW.md`
- Modify: `WORK/RESULTS.json`

**Interfaces:**
- Produces: CLI `materialize --out PATH --seed 0 --demos 3 --queries 4`, `materialize(...) -> report`, and `verify_tree(...) -> report`.

- [x] Add tests requiring three private episodes, three opaque public challenges, three exact Racket programs, 9 demonstrations, 12 queries, zero ambiguities, source/file receipts, replay verification, and refusal to overwrite an existing output directory.
- [x] Run new tests and confirm missing-interface failures.
- [x] Implement the evidence writer/verifier and CLI, then document the exact packet command and limits.
- [x] Run focused tests, materialize retained evidence under `WORK/checks/parametric/`, and run its verifier.
- [x] Run a bounded adversarial pass over parameter/Racket parity and public/private export.
- [x] Record exact commands, hashes, statuses, and unresolved limits in packet reports.
