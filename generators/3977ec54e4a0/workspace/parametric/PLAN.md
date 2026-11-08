# Parametric Chevron Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Deliver a bounded, reproducible, task-local eight-setting Racket prototype with complete private/public evidence.

**Architecture:** Guarded transformations of the pinned canonical program supply labels through RacketBridge. The selected generator supplies inputs; a diagnostic mirror and checked adaptations of declared competitors verify a finite demonstration-only gate.

**Tech Stack:** Python 3, pytest, included offline Racket, reviewer_support.

**Spec:** `DESIGN.md` and `WORK/PARAMETRIC-RULES.md`.

## Global Constraints

- Only `workspace/parametric/**`, the new focused test, and `WORK/checks/parametric/**` are owned here.
- Canonical setting `(fill_color=8, fill_edges=True)` preserves exact authority bytes.
- Colors are exactly `(2,4,6,8)`; edge setting is an actual boolean.
- Three demonstrations minimum; four queries by default; no repeated inputs.
- All labels and parameter rivals execute in Racket; private outputs never enter public queries.
- User authorized autonomous execution; no plan approval pause or broad library test run.
- This extracted packet has no git repository; retain exact source hashes and red/green logs instead of commits.

## Review Focus

- Boolean/float scalar coercions must fail closed before runtime execution.
- Canonical source drift must reject materialization rather than silently replacing new text.
- Complete arms can hide edge inclusion; an explicit sparse-arm probe must detect ambiguity.
- Source changes during evidence generation must fail rather than misbind provenance.
- Rejection bounds must return a documented failure without shortened/cloned queries.

## Task 1: Guarded rule materialization and reference execution

**Files:** create `prototype.py`; create `../../tests/test_parametric_chevrons.py`.

**Interfaces:** `Setting`, `SETTINGS`, `DEFAULT`, `canonical_rule()`, `materialize_rule(setting)`, `execute_rule(bridge, program, grid)`, `predict(grid, setting)`.

- [x] Write tests for exact canonical bytes, all canonical labels, four oriented strict-edge witnesses, and invalid parameters/source drift.
- [x] Run focused pytest through `review.py run`; retain expected missing-prototype RED result.
- [x] Implement the narrow source guards, reference executor, and independent diagnostic mirror.
- [x] Run those tests through real Racket and retain GREEN evidence (15 passed).

## Task 2: Identifiable deterministic episodes

**Interfaces:** consumes Task 1; produces `build_episode(seed, train=3, test=4, setting=None, max_attempts=128, bridge=None)` with `public`, `private`, and `report`; `EpisodeBuildError` retains failure evidence; `diagnostic_probe(bridge)` supplies designed ambiguity.

- [x] Write tests for all eight 3+4 episodes, actual index replay, identical reruns/fresh objects, finite rivals, strict counts, and bounded failure.
- [x] Write the complete-arm/sparse-arm ambiguity test and retain a RED run.
- [x] Implement the bounded demo-only selection gate and adapt/check all declared competitors.
- [x] Run focused tests and retain GREEN evidence (28 passed, CLI deselected).

## Task 3: Evidence CLI and final verification

**Interfaces:** consumes Task 2; CLI accepts `--seed --train --test --fill-color --fill-edges --all-settings --out` and refuses existing destinations.

- [x] Write and run a CLI test asserting complete public/private artifacts, all eight exact program files, hashes, and malformed argument failure.
- [x] Implement CLI, source snapshots, canonical parity receipt, and concise README (one CLI test passed).
- [x] Execute all-eight-setting evidence with the final selected generator source; record exact commands in `WORK/checks/parametric/commands.json`.
- [x] Run the complete focused prototype tests; inspect logs and source bindings before claiming completion.

## Progress and rulings

- Pre-flight: Task 2 consumes Task 1's validated setting and executor; Task 3 consumes the deterministic episode result. No interface conflicts found.
- Ruling: do not use git worktrees/commits because this extracted packet contains no `.git`; keep tests and source-bound evidence in the requested task scope.
- Ruling: the user's explicit task bounds verification to relevant prototype tests; do not run the broad library suite.
- Task 1 complete: `tdd-red.log` -> `tdd-green-rule.log` (15 passed). The first missing-file scaffold run reported fixture errors; it was rerun with a direct assertion and the retained RED is one assertion failure.
- Task 2 complete: `tdd-red-episode.log` (10 failures for absent APIs) -> `tdd-green-episode.log` (28 passed).
- Task 3 complete: `tdd-red-cli.log` (missing artifact) -> `tdd-green-cli.log` (1 passed); `final-tests.log` (30 passed) and `all-settings/private/report.json` (eight complete 3+4 episodes).
- Ruling: use shared exported comment/wrapper helpers plus lexical `h/w` for this pinned canonical syntax. The general `wrap_rule` converter imports a private `scripts` namespace that is unavailable in the direct library payload; no shared runtime interfaces were changed.
- Final verification: `integrity-report.json` independently verified all twelve source hashes, all eight program hashes, neutral public/private schemas, actual accepted indices `0..6`, sixteen finite rival scores per episode, and 56 unique inputs across the retained eight episodes.
- Failure verification: `bounded-failure/private/failure.json` records the requested bound of one attempt, no accepted lesson, and no public challenge. Exit code 1 is expected, not a failed positive claim.
- Final source binding: selected generator `406ea39bd1050f238678d02ce90c50e02a8dd6e24e214d739398783ec7c5e603`; Racket canonical `b4c2540796af088ba41f486413b1be85ff6f8a9db373d30e6105bdc4529c7f25`.
- Independent code review: completed after source freeze; no Critical or Important issue found and no source change requested. See WORK/checks/final-review/review.md for the independent 17-call compatibility check, duplicate/short-query failures, five real-Racket geometry tests, and retained-artifact inspection.
