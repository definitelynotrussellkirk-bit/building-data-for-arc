# Procedural Maze Diversity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair task `44690b1b635f` so its generated training distribution contains many source-valid wall topologies rather than a palette-reskinned table of 42 fixed semantic masks.

**Architecture:** Preserve the canonical Racket rule, public anchors, and existing 13 named fixed profiles. Add one source-valid `procedural_maze` profile generated as a deterministic perfect maze from the existing keyed RNG, validate its structural grammar in `_analysis`, and include it in ordinary sampling without weakening current invariants. Keep proposed rule variants in a separate parametric prototype.

**Tech Stack:** Python 3.12+, pytest, standard library only; Racket evidence remains an official-packet replay step.

**Spec:** Recovered immutable assignment `review-efb25880f190b5c1` and retained audit finding in task `44690b1b635f/evidence/review_index.json`.

## Global Constraints

- Edit only task-local/recovery files; do not change the canonical rule or `RULE_HASH`.
- Preserve exact public masks and canonical outputs.
- Every random choice must use `GenCtx.draw_rng` or another keyed draw.
- `scene_profile=procedural_maze` must be observable, deterministic, validator-accepted, and source-valid.
- Do not claim official packet battery/Racket/package verification when unavailable.

## Review Focus

- Numeric task package import must use `importlib`, not dotted syntax.
- Procedural topology must vary after semantic color normalization.
- Structural validator must reject malformed lattice mazes rather than accepting arbitrary grids.
- Existing fixed profiles and public anchors must remain byte-for-byte behavior compatible.
- Generated outputs must match an independent BFS oracle for every tested seed and band.

---

### Task 1: Procedural topology profile

**Files:**
- Modify: `puzzle_generators/per_puzzle/44690b1b635f/generator.py`
- Test: `tests/test_role_topology_diversity.py`

**Interfaces:**
- Produces: `scene_profile="procedural_maze"`, deterministic generated grids, and `_analysis(...)["scene_profile"] == "procedural_maze"`.

- [ ] Write and run a failing test showing the profile is absent and normalized support is fixed.
- [ ] Implement deterministic DFS perfect-maze construction and a strict structural recognizer.
- [ ] Add independent oracle, malformed-maze, deterministic, and default-distribution tests.
- [ ] Run the focused suite to green.

### Task 2: Parametric prototype and handoff tooling

**Files:**
- Create: `generators/44690b1b635f/workspace/parametric/prototype.py`
- Create: `generators/44690b1b635f/workspace/parametric/README.md`
- Create: `tests/test_parametric_prototype.py`
- Create: `tools/replay_in_full_packet.py`

**Interfaces:**
- Produces: fixed-per-episode `neighbor_mode` and `phase` settings, separate demo/query counts, four distinct queries, and a future-agent replay command list.

- [ ] Write failing prototype tests for canonical default, alternate settings, fixed episode settings, and four distinct queries.
- [ ] Implement the minimal prototype and evidence serializer.
- [ ] Add a full-packet replay helper that checks source hash, copies patch files, and prints/runs official commands.
- [ ] Run prototype tests to green.

### Task 3: Review records and deliverable

**Files:**
- Create: `REVIEW.md`, `DECISIONS.md`, `QUESTION_ANSWER.md`, `FEEDBACK_TO_CODEX.md`, `AUDIT.md`, `RESULTS.json`
- Update: `generators/44690b1b635f/notes.md`
- Create: recovery blind-solve record and evidence logs

- [ ] Record exact implemented changes, commands, hashes, measured diversity, and explicit unavailable official checks.
- [ ] Answer `qwen9-data-value` with a normalized-template shortcut gate.
- [ ] Perform whole-package self-review and run all local tests.
- [ ] Build and verify a source-bound recovery ZIP.
