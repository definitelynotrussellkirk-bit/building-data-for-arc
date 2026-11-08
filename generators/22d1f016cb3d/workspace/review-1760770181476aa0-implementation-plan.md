# 22d1f016cb3d Review Repair and Parametric Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:executing-plans` and `superpowers:test-driven-development`; the immutable packet and return builder replace Git worktree/commit mechanics.

**Goal:** Return an admissible ARCpuzzles review package that fixes measured canonical-generator gates, adds a bounded fixed-per-episode rule variant with exact Racket evidence, completes the exposed solve and two audits, and passes fresh-packet replay.

**Architecture:** Keep the selected canonical rule byte-authoritative and change only its Python input sampler/contract. Add strict call-argument validation, rebalance default scene-profile sampling toward canonical 10×10/two-color support, and declare executable local-rule rivals without changing labels. Place the output-palette rule variant entirely under `workspace/parametric/`, with exact Racket programs, private evidence, public challenges, and prototype-only tests.

**Tech Stack:** Python 3.12+, pytest, the packet's `review.py` wrapper, `reviewer_support`, and the pinned offline Racket bridge.

**Spec:** `WORK/PARAMETRIC-RULES.md`, `WORK/ARC-DESIGN.md`, and the ordered assignment printed by `python3 review.py duties`.

## Global Constraints

- Preserve canonical `RULE_HASH = "2219db85ca5f"` and canonical input/output behavior.
- Edit only `generators/22d1f016cb3d/`, task-local handoff files, solve lanes, audit evidence, and check receipts permitted by the packet.
- New tests live under `generators/22d1f016cb3d/tests/`; the selected canonical execution path must not depend on prototype code.
- Hidden rule parameters are chosen once per episode and held fixed across every demonstration and query.
- Exact Racket execution, not a Python mirror alone, is label authority for prototype evidence.
- Preserve failed/blocked attempts and record exact commands, working directories, exits, hashes, and limitations.

## Review Focus

- `bool`, float, string, and negative call scalars must be rejected rather than hashed/coerced.
- Every difficulty band must retain at least one exact 10×10/two-color canonical-profile draw; pooled support must clear the packet floor without eliminating generalized profiles.
- A neighbor-degree shortcut must fit all canonical solid rectangles yet fail a retained straight-degree-two/local-neighbor witness.
- A lesson rival that collapses edge (`4`) cells into end/corner (`1`) cells must be refuted by every lawful generated input.
- Public prototype challenge files must contain labelled demonstrations but no hidden parameter, Racket source, or query output.

---

### Task 1: Canonical Generator Gate Repair

**Files:**
- Modify: `generators/22d1f016cb3d/tests/test_generator_22d1f016cb3d.py`
- Modify: `generators/22d1f016cb3d/generator.py`
- Modify: `generators/22d1f016cb3d/notes.md`
- Create: `generators/22d1f016cb3d/counterexamples/degree-straight-segment.json`

**Interfaces:**
- Produces strict `generate(seed: int, sample_index: int, ...)`, unchanged `rule_mirror`, `strict_canonical_like`, executable semantic declarations, and a default profile mixture that passes the canonical-profile floor.
- Task 2 consumes the unchanged production generator and canonical source only; it must not import prototype code into production.

- [ ] Add failing tests for invalid seed/sample-index scalars, per-band canonical-envelope support, the canonical-fitting neighbor-degree shortcut, its straight-segment witness, and the always-distinguished edge-collapse lesson competitor.
- [ ] Run the selected tests and retain the RED output showing current scalar acceptance, low support, and missing semantic declarations.
- [ ] Implement exact scalar validation, bump the sampler version, rebalance public/general profile weights, add semantic witness/rival hooks, and retain a minimal straight-segment counterexample.
- [ ] Run the selected tests GREEN, then run the complete task-local canonical test file.

### Task 2: Fixed-per-Episode Boundary-Palette Prototype

**Files:**
- Create: `generators/22d1f016cb3d/tests/test_parametric_boundary_palette.py`
- Create: `generators/22d1f016cb3d/workspace/parametric/prototype.py`
- Create: `generators/22d1f016cb3d/workspace/parametric/README.md`
- Create: `generators/22d1f016cb3d/workspace/parametric/racket/ends1_edges4.rkt`
- Create: `generators/22d1f016cb3d/workspace/parametric/racket/ends4_edges1.rkt`
- Create: `generators/22d1f016cb3d/workspace/parametric/examples/*.json`
- Create: `WORK/checks/parametric/*`

**Interfaces:**
- Produces `choose_boundary_palette(seed)`, `racket_source(mode, root)`, `python_transform(grid, mode)`, `build_episode(root, seed)`, `public_challenge(episode)`, and a CLI that executes both exact Racket programs and writes evidence.
- Consumes Task 1's unchanged canonical rule and production generator, but remains prototype-only.

- [ ] Add a failing prototype test suite whose first assertion reports the missing prototype path.
- [ ] Run it RED and retain the failure.
- [ ] Implement two bounded modes: canonical/default `ends1_edges4` and proposed `ends4_edges1`, swapping only the zero-opposing-pair and exactly-one-opposing-pair output colors while preserving source color, interior color, local pair tests, non-5 preservation, and all input roles.
- [ ] Materialize exact Racket files; build four-demo/one-query episodes for even and odd seeds; require every demonstration and query to distinguish the alternative mode; write public challenges with hidden fields removed.
- [ ] Execute both Racket rules through the pinned bridge, compare every label with the Python assertion mirror, retain hashes/evidence, and run the prototype tests GREEN.

### Task 3: Required Generator Verification

**Files:**
- Create/update: `WORK/checks/after/`, `WORK/checks/task-tests/`, `WORK/checks/lesson-census*.json`, `WORK/checks/lint/`

**Interfaces:**
- Consumes Tasks 1–2; produces finished check receipts and measured remaining limitations for handoff.

- [ ] Run the strict after battery and read every stage verdict.
- [ ] Run the isolated selected task tests.
- [ ] Run the 100-per-band rotated-query lesson census; retain any ambiguity and repair only source-caused defects.
- [ ] Run the focused lint stage and prototype verification command from the outer packet wrapper.

### Task 4: Exposed Solve and Adversarial Audits

**Files:**
- Modify/create: `WORK/solve/*`, `WORK/AUDIT.md`, `WORK/checks/audit/*`

**Interfaces:**
- Consumes the repaired generator but obeys visible-only solve restrictions; produces frozen solve revisions and two findings-only audit sections.

- [ ] Prepare the post-repair challenge, solve from visible examples without opening its Racket/reference/private labels, record revisions, check visible examples, and finish honestly with earlier exposure `yes`.
- [ ] Draw the two audit targets once, inspect their current source/evidence, create concrete reproductions or record `No issue found`, and do not edit audited sources.

### Task 5: Handoff, Fresh Replay, and Packaging

**Files:**
- Modify/create: `WORK/REVIEW.md`, `WORK/DECISIONS.md`, `WORK/QUESTION_ANSWER.md`, `WORK/FEEDBACK_TO_CODEX.md`, `WORK/RESULTS.json`
- Create: generated `WORK/review_response_review-1760770181476aa0.zip`

**Interfaces:**
- Consumes all prior receipts and source hashes; produces the only user-facing return artifact.

- [ ] Write the one-minute acceptance summary, decision/reversal ledger, Qwen9 data-quality answer, prioritized tooling feedback, exact command receipts, curriculum annotation, remaining limits, and stopping reason.
- [ ] Run the packet's reviewer-owned final handoff check, including fresh-packet patch replay, final source hash, focused tests, and concise self-review.
- [ ] Package with `review.py package`, inspect `INTAKE.json` and ZIP members, independently verify hashes and replay commands, and return only the generated response ZIP.
