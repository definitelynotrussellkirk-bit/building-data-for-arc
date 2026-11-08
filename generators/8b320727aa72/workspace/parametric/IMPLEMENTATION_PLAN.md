# Disagreement-Action Prototype Implementation Plan

> **For agentic workers:** execute task-by-task with test-driven development. This packet is not a git repository, so verification receipts and the progress ledger replace commits.

**Goal:** Repair the canonical generator's explicit contracts and create a runnable, Racket-labeled `mark|restore` episode prototype without altering canonical execution.

**Architecture:** The selected generator gains only validation and semantic-contract helpers. A separate task-local prototype imports that generator for lawful inputs, selects one rule setting per episode, executes exact Racket through the packaged bridge, and emits private/public evidence artifacts.

**Tech Stack:** Python 3.12, pytest, packaged `arcpuzzles` runtime and Racket bridge.

**Spec:** `generators/8b320727aa72/workspace/parametric/DESIGN.md`

## Global Constraints

- Canonical `RULE_HASH` stays `065574e7466b`.
- Selected canonical generation and outputs do not change.
- Frozen `tests/test_generator_8b320727aa72.py` is not edited.
- Proposed variants stay under `workspace/parametric/`.
- All prototype labels come from executing Racket.

## Review Focus

- `bool`, float, string, negative index, invalid difficulty, and unknown override inputs fail loudly.
- Existing exact override boundaries and deterministic replay remain valid.
- Semantic rival functions never mutate inputs and agree with hand-derived expected grids.
- Episode parameter is fixed across demos/query, and public output leaks no hidden setting or query answer.
- Canonical Racket text is exact while restore Racket executes successfully on the same lawful input.

---

### Task 1: Canonical Input Contract and Semantic Hooks

**Files:**
- Modify: `generators/8b320727aa72/generator.py`
- Create: `generators/8b320727aa72/tests/test_review_repair.py`

**Interfaces:**
- Produces: strict `generate(seed, sample_index, *, difficulty=None, **overrides)` validation; `_canonical_mark_output(grid)`; `_restore_consensus_output(grid)`; semantic declaration dictionaries; `lesson_identifiable(demos, query)`.

- [ ] Write focused tests for invalid scalars/unknown keys, valid boundaries, canonical/restore output literals, witness/rival disagreement, and lesson scoring.
- [ ] Run the new test file and confirm failures are caused by missing validation/hooks.
- [ ] Implement minimal validation and semantic helpers.
- [ ] Run the new tests and frozen fixture; both pass.

### Task 2: Parametric Racket Prototype

**Files:**
- Create: `generators/8b320727aa72/workspace/parametric/prototype.py`
- Create: `generators/8b320727aa72/workspace/parametric/README.md`
- Create: `generators/8b320727aa72/tests/test_parametric_disagreement_action.py`

**Interfaces:**
- Produces: `PARAMETER_VALUES`, `CANONICAL_RULE`, `rule_for(action)`, `choose_parameters(seed)`, `execute_rule(rule, grid)`, `materialize_episode(...)`, and CLI evidence generation.

- [ ] Write tests for exact canonical text, deterministic episode-wide choice, Racket parity on hand-derived witness outputs, rival-refuting demonstrations, and public masking.
- [ ] Run tests and confirm missing-module failure.
- [ ] Implement the minimal prototype and README command.
- [ ] Run focused tests and materialize retained evidence under `WORK/checks/parametric/`.

### Task 3: Selected Authority Text Synchronization

**Files:**
- Tool-generated task-specific solution JSON changes and recovery receipt only.

**Interfaces:**
- Consumes: current canonical `program_solution`.
- Produces: selected `target_code` exact equality; archival `raw_code` unchanged.

- [ ] Generate a dry-run `authority-sync --selected-only` proposal.
- [ ] Inspect that only active `target_code` pointers change to canonical text.
- [ ] Apply the exact reviewed proposal and retain receipt.
- [ ] Run `authority_sync` and `rule_smoke`; both pass.

### Task 4: Full Verification and Handoff

**Files:**
- Modify: `generators/8b320727aa72/notes.md`
- Create/update: packet reports and evidence.

- [ ] Run task tests, complete after battery, and 100-lessons-per-band rotating census.
- [ ] Perform post-repair visible-only solve without reopening rule/generator during solve.
- [ ] Complete question answer, two assigned audits, decisions, review, feedback, and results records.
- [ ] Package with `review.py package` and inspect the resulting archive.
