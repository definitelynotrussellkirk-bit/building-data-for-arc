# Destination Edge Parametric Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify a task-local `destination_edge=bottom|top` prototype with episode-consistent hidden semantics and Racket-derived labels.

**Architecture:** Keep the selected production generator untouched. A focused prototype imports it only to produce lawful inputs, reads static task-local Racket rules, labels complete episodes through the included Racket bridge, checks the opposite parameter as a rival, and emits private evidence plus masked public challenges.

**Tech Stack:** Python 3.12+, pytest, task-local `reviewer_support`, `arc_repl.racket_bridge.RacketBridge`, Racket grid DSL.

**Spec:** `generators/44d20451ce17/workspace/parametric/DESIGN.md`

## Global Constraints

- Modify only `generators/44d20451ce17/`, its task tests, and reviewer-owned report/evidence files.
- Do not alter the selected canonical generator behavior, `RULE_HASH`, catalog approval, or shared runtime interfaces.
- `bottom` must preserve the exact canonical Racket program bytes.
- Choose `destination_edge` once per episode; never per pair.
- Public challenge files must omit hidden parameters, rule text, and query answers.
- Public filenames and IDs must be derived only from exact visible challenge bytes;
  reject duplicates and sort batch writes by public ID.
- All retained labels must be executed by Racket; a Python mirror is verification only.

## Review Focus

- A source `1` already on the chosen edge must not create duplicate markers.
- Multiple source `1`s in one column must collapse to one edge marker.
- Non-`1` cells must be preserved except where the edge marker overwrites one cell.
- Opposite-edge demonstrations must differ before any query that differs.
- Invalid parameter values and malformed public/private episode structures must fail loudly.

---

### Task 1: Pin prototype behavior with failing tests

**Files:**
- Create: `generators/44d20451ce17/tests/test_parametric_destination_edge.py`

**Interfaces:**
- Consumes: planned module `workspace/parametric/prototype.py`.
- Produces: executable expectations for rule bytes, episode selection, Racket parity, rival distinguishability, masking, determinism, and invalid values.

- [ ] Write tests importing the prototype by path and asserting `bottom` is byte-for-byte canonical.
- [ ] Add tests for deterministic episode-level parameter selection covering both values.
- [ ] Add Racket/Python parity tests on canonical and repeated-column inputs.
- [ ] Add complete-episode rival and public masking tests.
- [ ] Run the focused file and confirm it fails because prototype interfaces do not yet exist.

### Task 2: Implement rules and episode materializer

**Files:**
- Create: `generators/44d20451ce17/workspace/parametric/prototype.py`
- Create: `generators/44d20451ce17/workspace/parametric/rules/bottom.rkt`
- Create: `generators/44d20451ce17/workspace/parametric/rules/top.rkt`
- Create: `generators/44d20451ce17/workspace/parametric/README.md`

**Interfaces:**
- Produces: `parameters(seed)`, `racket_source(edge)`, `apply_python(grid, edge)`, `apply_racket(grid, edge, bridge=None)`, `build_episode(seed, ...)`, `parameter_rival_findings(episode)`, `public_challenge(episode)`, and `build_evidence(...)`.

- [ ] Materialize exact canonical `bottom.rkt` and a one-predicate `top.rkt` variant.
- [ ] Implement strict parameter validation and a deterministic one-draw episode selector.
- [ ] Build three demonstrations and four distinct queries from alternating
  selected-generator profiles, with all seven inputs distinct.
- [ ] Execute labels with one reusable Racket bridge and retain source/rule hashes.
- [ ] Reject episodes where the query needs a distinction absent from demonstrations.
- [ ] Emit masked public challenges and a private evidence report.
- [ ] Run focused tests until all pass.

### Task 3: Retain reproducible evidence and integrate reviewer handoff

**Files:**
- Create: two opaque visible-content-ID files under
  `generators/44d20451ce17/workspace/parametric/examples/`
- Create: `WORK/checks/parametric/destination-edge-evidence.json`
- Modify: `generators/44d20451ce17/notes.md`
- Modify: reviewer-owned `WORK/REVIEW.md`, `WORK/DECISIONS.md`, `WORK/RESULTS.json`, and `WORK/QUESTION_ANSWER.md`.

**Interfaces:**
- Consumes: `prototype.py --out ... --public-dir ...`.
- Produces: exact replay artifacts and a handoff that separates canonical status from proposed prototype status.

- [ ] Run the prototype through `review.py run` and retain its command/result.
- [ ] Verify both parameter values, exact default preservation, four Racket-labelled
  queries per setting, all-input uniqueness, per-query rival distinction, shared
  witness disagreement, public masking, and visible-byte-derived filenames.
- [ ] Run task-local tests and applicable canonical checks.
- [ ] Document bounded scope, source exposure, limitations, and unchanged canonical authority.
