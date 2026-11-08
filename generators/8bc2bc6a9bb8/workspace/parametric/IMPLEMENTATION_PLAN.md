# Sort-Key Parametric Family Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Repair the canonical footprint-ranking teaching shortcut and build a promotion-ready, Racket-verified `occupied_area|bbox_area` parametric family with four-query public/private export evidence.

**Architecture:** Keep the selected production generator and canonical authority intact except for a constructive sampling/teaching repair. Place all proposed rule-variant code under the task-local `workspace/parametric/`, with one module owning sampling, execution, certificates, and evidence, plus a thin adapter contract.

**Tech Stack:** Python 3.12, pytest/unittest, bundled Racket bridge, existing `reviewer_support` and `puzzle_generators` runtime helpers.

**Spec:** `generators/8bc2bc6a9bb8/workspace/parametric/DESIGN.md`

## Global Constraints

- Work only in assigned task homes and required packet return files.
- Preserve the canonical default Racket program byte-for-byte.
- Support `2..6` demos and `1..8` queries independently; evidence uses `3/4`.
- Every label is executed through the matching Racket program.
- Public identifiers hash only visible demonstration inputs/outputs and query inputs.
- The packet has no `.git`; each task ends with a retained verification log instead of a commit.

## Review Focus

- Area/footprint order reversal must be constructive, not probabilistic.
- The 30×30 query must use boundary contacts and broad spatial spread, not empty padding.
- Count boundaries must reject booleans, floats, zero, and out-of-range integers.
- A private setting, seed, program, or query-answer change must not change the public ID.
- Identifiability must use demonstrations only and fail closed when a rival survives.

---

### Task 1: Canonical footprint-shortcut repair

**Files:**
- Modify: `generators/8bc2bc6a9bb8/tests/test_generator_8bc2bc6a9bb8.py`
- Modify: `generators/8bc2bc6a9bb8/generator.py`

**Interfaces:**
- Produces: `SEMANTIC_RIVALS["footprint_then_area"]`, witness mapping, and a schedule profile that constructively reverses area and footprint order.

- [x] Add a regression asserting the new rival survives the old finite bank but is refuted by one generated four-profile lesson, and assert the conflict profile exposes opposite `sorted_sizes` and footprint order.
- [x] Run the focused test and verify RED because the rival/witness does not exist.
- [x] Add the five-cell line, a profile-fixed five-line/four-L pair, footprint observables, rival, witness, and mappings with no canonical rule change.
- [x] Run the focused task test and verify GREEN.
- [x] Save the command output under `WORK/checks/8bc2bc6a9bb8-canonical-repair/`.

### Task 2: Parametric program and episode core

**Files:**
- Create: `generators/8bc2bc6a9bb8/tests/test_parametric_sort_key.py`
- Create: `generators/8bc2bc6a9bb8/workspace/parametric/prototype.py`

**Interfaces:**
- Produces: `canonical_source()`, `program_for(sort_key)`, `execute_rule()`, `python_apply()`, `validate_input()`, `make_episode(seed, sort_key, demos, queries)`, `public_bytes()`, `public_id()`.

- [x] Write tests for exact canonical default, guarded alternate Racket materialization, a literal order-reversal witness, fixed-setting deterministic episodes, same inputs across settings, distinct counts, four queries, and an exact 30×30 query.
- [x] Run the new test file and verify RED because `prototype.py` is absent.
- [x] Implement strict setting/seed/count validation and exact canonical source loading.
- [x] Implement the alternate footprint-primary comparator by guarded source transformation.
- [x] Implement setting-neutral deterministic profile sampling with constructive order reversals and a substantive 30×30 profile.
- [x] Execute every pair through Racket, compare with an independent Python diagnostic, and retain demonstration-only rival results.
- [x] Run the new tests and verify GREEN.
- [x] Save the command output under `WORK/checks/parametric/sort-key-core/`.

### Task 3: Public projection, evidence writer, and promotion adapter

**Files:**
- Modify: `generators/8bc2bc6a9bb8/tests/test_parametric_sort_key.py`
- Modify: `generators/8bc2bc6a9bb8/workspace/parametric/prototype.py`
- Create: `generators/8bc2bc6a9bb8/workspace/parametric/adapter.py`
- Create: `generators/8bc2bc6a9bb8/workspace/parametric/promotion.json`
- Create: `generators/8bc2bc6a9bb8/workspace/parametric/README.md`
- Create: `generators/8bc2bc6a9bb8/workspace/parametric/adversarial_probe.py`

**Interfaces:**
- Produces: `write_evidence(...)`, CLI, promotion `program(settings)` and `generate(seed, settings, demos, queries)`.

- [x] Add tests for masked query outputs, visible-byte IDs, private-field invariance, existing-output refusal, adapter contract, boundary counts, exact integer cells, and sequential first-turn projection.
- [x] Run the tests and verify RED because writer/adapter/probe are absent.
- [x] Implement public projection and atomic evidence writing with hash-bound files.
- [x] Implement the thin adapter and bounded promotion contract.
- [x] Implement the two-surface adversarial probe and document exact commands and limits.
- [x] Run tests, generate two setting episodes at `3/4`, run the adversarial probe, and validate public exports.
- [x] Create the native parametric evidence manifest with explicit included test source and actual reported checks.

### Task 4: Secondary target robustness checks

**Files:**
- Modify: `generators/be5d9fa6fec1/tests/test_generator.py`
- Modify: `generators/be5d9fa6fec1/generator.py`
- Create evidence only under: `WORK/checks/6fde852adb54-robustness/`

**Interfaces:**
- Produces: strict unknown-difficulty behavior for `be5d9fa6fec1`; a source-bound bounded outcome for `6fde852adb54`.

- [x] Add a `be5d9fa6fec1` regression asserting unknown difficulty raises `ValueError`; run RED.
- [x] Add the minimal explicit difficulty validation; run GREEN.
- [x] Build and run a bounded fresh-process `6fde852adb54` probe covering invalid controls, malformed short grids, deterministic replay, and several canonical/generalized Racket-mirror cases.
- [x] Change `6fde852adb54` only if the probe finds a clear local defect; otherwise record unchanged with the source hash and probe result.

### Task 5: Handoff, verification, and packaging

**Files:**
- Modify: each selected task's `notes.md` as needed
- Create: `WORK/REVIEW.md`
- Create: `WORK/FEEDBACK_TO_CODEX.md`
- Modify: `WORK/RESULTS.json`

**Interfaces:**
- Produces: complete three-target repair rows, exact command records, evidence paths, limits, and one packaged delta ZIP.

- [x] Run changed-target staged tests and the prototype-focused tests with the bundled Racket runtime.
- [x] Run the bounded adversarial checks and inspect the generated evidence files.
- [x] Record source hashes, commands, exit codes, outcomes, remaining limits, and the main `parametric_work` row.
- [x] Write the short handoff and one friction/mitigation item.
- [x] Run `review.py status`, `review.py package`, inspect the ZIP member list, and rerun any package validation requested by the wrapper.
