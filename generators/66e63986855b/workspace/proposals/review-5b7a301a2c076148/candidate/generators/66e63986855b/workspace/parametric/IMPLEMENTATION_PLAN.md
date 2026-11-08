# Reflection Extent Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use test-driven development and execute this plan task-by-task.

**Goal:** Build a Racket-backed, task-local `reflection_extent ∈ {1,2}` prototype with independently configurable demonstration/query counts, masked public exports, and compact reproducible evidence.

**Architecture:** `prototype.py` loads the exact canonical rule, materializes the extent-1 rule through one guarded structural substitution, executes both through `RacketBridge`, samples lawful inputs from the selected generator, certifies the opposite setting is refuted by demonstrations, and writes separate public/private evidence. The production generator and canonical authority remain untouched.

**Tech Stack:** Python 3.12+, pytest, repository `reviewer_support`, `arc_repl.racket_bridge`, bundled Racket runtime.

**Spec:** `generators/66e63986855b/workspace/parametric/DESIGN.md`

## Global Constraints

- Edit only files under `generators/66e63986855b/` plus assignment reports/evidence.
- `reflection_extent=2` must return the canonical program byte-for-byte.
- Every output label and counterfactual used as evidence must be executed in Racket.
- Default retained episodes use 3 demonstrations and 4 distinct queries.
- Public identifiers depend only on exact visible challenge bytes.
- No production generator, canonical rule, rule hash, approval, or training state changes.
- The extracted packet has no Git metadata; verification hashes and command receipts replace commit steps.

## Review Focus

- Boolean/string/fractional settings or counts must be rejected rather than coerced.
- The canonical substitution site must occur exactly once or materialization must fail closed.
- Duplicate visible inputs/public payloads must be rejected, not silently reused.
- Public output must omit setting, seed, Racket source, rival outputs, and query answers.
- Rival certification must use demonstration labels only and separately verify all four queries differ.

---

### Task 1: Write the failing behavioral contract

**Files:**
- Create: `generators/66e63986855b/tests/test_parametric_reflection_extent.py`

**Interfaces:**
- Consumes: selected generator and bundled Racket bridge.
- Produces: executable expectations for `canonical_program`, `program_for_extent`, `apply_python`, `apply_racket`, `choose_parameters`, `build_episode`, `public_challenge`, and `materialize`.

- [ ] Add literal witness tests proving extent 1 and 2 have hand-derived different outputs and extent 2 is exact canonical text.
- [ ] Add validation tests for settings, counts, and deterministic once-per-episode selection.
- [ ] Add two complete episode tests with 3 demos and 4 queries, distinct lawful inputs, Racket labels, and demonstration-only rival refutation.
- [ ] Add public masking/identifier tests and materializer failure tests.
- [ ] Run the focused test and observe failure because the prototype is absent.

### Task 2: Implement the minimal prototype core

**Files:**
- Create: `generators/66e63986855b/workspace/parametric/prototype.py`

**Interfaces:**
- Produces:
  - `canonical_program(root=None) -> str`
  - `validate_extent(value) -> int`
  - `program_for_extent(extent, root=None) -> str`
  - `apply_python(grid, extent) -> list[list[int]]`
  - `apply_racket(grid, extent, bridge=None) -> list[list[int]]`
  - `choose_parameters(seed) -> dict[str, int]`
  - `build_episode(seed, *, demos=3, queries=4, extent=None, bridge=None) -> dict`
  - `public_challenge(episode) -> dict`
  - `materialize(out, *, demos=3, queries=4, episode_seeds=(0,1), bridge=None) -> dict`

- [ ] Implement strict validation and guarded Racket materialization.
- [ ] Implement the independent Python reference and real Racket execution.
- [ ] Sample setting-independent lawful inputs, rejecting duplicates and retry exhaustion.
- [ ] Build episodes and certify the opposite setting is refuted using only demonstrations.
- [ ] Run the focused test to green; then refactor without changing behavior.

### Task 3: Add evidence writer, CLI, and user-facing instructions

**Files:**
- Modify: `generators/66e63986855b/workspace/parametric/prototype.py`
- Create: `generators/66e63986855b/workspace/parametric/README.md`

**Interfaces:**
- CLI: `prototype.py --out PATH --demos N --queries N --episode-seeds ...`
- Output: `report.json`, `private/programs/*.rkt`, `private/episodes/*.json`, `private/witness.json`, and `public/<visible-sha256>.json`.

- [ ] Make the writer refuse an existing/nonempty output directory.
- [ ] Write programs and private episodes before masked public challenges; sort public records by ID.
- [ ] Record source/runtime hashes, exact commands, counts, and bounded limitations.
- [ ] Add CLI count regression and run focused tests to green.

### Task 4: Execute scoped verification and adversarial checks

**Files:**
- Evidence: `../checks/parametric/reflection-extent-v1/`

- [ ] Run focused parametric tests through `review.py run`.
- [ ] Materialize two episodes with 3 demos and 4 queries through bundled Racket.
- [ ] Adversarially inspect parameter/Racket parity and public/private leakage/duplicate rejection.
- [ ] Run the selected generator's existing 34 tests to prove canonical scope remains green.
- [ ] Record exact outputs, failures, hashes, and limits.

### Task 5: Complete assignment records and package

**Files:**
- Modify: `generators/66e63986855b/notes.md`
- Create/modify: `REVIEW.md`, `RESULTS.json`, optional `FEEDBACK_TO_CODEX.md`

- [ ] Draw and complete exactly the two supplementary tickets.
- [ ] Record structured ticket rows and evidence paths.
- [ ] Write the short repair brief with canonical/prototype separation and unresolved limits.
- [ ] Run package validation and create the required delta ZIP.
