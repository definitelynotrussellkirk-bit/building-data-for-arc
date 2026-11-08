# 148acacd84d9 Rotate-Then-Gravity Parametric Implementation Plan

> **For agentic workers:** execute each task with test-first development and fresh verification.

**Goal:** Add a native two-setting parametric family whose default is the exact canonical whole-canvas clockwise rotation and whose alternate first rotates, then packs payload colors toward the border selected by the rotated marker.

**Architecture:** `adapter.py` is the native entry point. It delegates deterministic scene construction and Python claim labels to `prototype.py`, while exact Racket programs live in `rules.py`. Inputs are setting-neutral square scenes with one border marker (color 9) and multicolor payload; demo/query prefixes are stable and include a substantive 30×30 query. `self_audit.py` executes the selected programs and finite rival programs through protected Racket. Native qualification remains the authority for labels and finite setting identification.

**Tech stack:** Python 3.12+, pytest, ARCpuzzles native parametric worker, protected Racket DSL.

**Spec:** `START-HERE.md`, `WORK/PARAMETRIC-RULES.md`, and assignment `review-74ba6822a552718e`.

## Global constraints

- Modify only `generators/148acacd84d9/` plus packet result/evidence files.
- Preserve `(rule! (rotate-cw g))` byte-for-byte as the default program.
- Support 2–6 demonstrations independently from 1–4 queries; normal production uses four queries.
- Keep settings/programs/query answers private; public projections reveal one query and no future-count hint.
- Use setting-neutral inputs, distinct pairs, stable prefixes, and protected-Racket qualification.
- Name and execute a changed-output wrong-intermediate causal witness.
- Do not claim owner acceptance or training admission.

## Review focus

1. Marker at each of four borders must select the corresponding post-rotation gravity edge.
2. Marker-line payload must pack around the fixed marker rather than overwrite it.
3. Two-demo lessons must uniquely distinguish the declared settings.
4. Query prefixes must remain identical when requesting one versus four queries.
5. The 30×30 scene must contain substantive payload across many lines, not padded emptiness.

---

### Task 1: Contract and deterministic scene grammar

**Files:**
- Create: `generators/148acacd84d9/tests/test_parametric_gravity.py`
- Create: `generators/148acacd84d9/workspace/parametric/prototype.py`
- Create: `generators/148acacd84d9/workspace/parametric/adapter.py`
- Create: `generators/148acacd84d9/workspace/parametric/promotion.json`
- Create: `generators/148acacd84d9/workspace/parametric/canonical.rkt`

**Interfaces:**
- `adapter.program(settings: dict) -> str`
- `adapter.generate(seed: int, settings: dict, demos: int = 3, queries: int = 4) -> dict`
- `prototype.public_turn(episode: dict, query_index: int = 0) -> dict`

- [ ] Write tests for exact default source, strict settings/count validation, setting-neutral matched inputs, distinct pairs, stable prefixes, public projection, and 30×30 content.
- [ ] Run the focused test and confirm missing-module failure.
- [ ] Implement only enough deterministic scene construction and adapter validation to pass.
- [ ] Run the focused test and confirm pass.

### Task 2: Exact rotate-then-gravity semantics

**Files:**
- Create: `generators/148acacd84d9/workspace/parametric/rules.py`
- Modify: `generators/148acacd84d9/workspace/parametric/prototype.py`
- Modify: `generators/148acacd84d9/tests/test_parametric_gravity.py`

**Interfaces:**
- `rules.program(settings: dict) -> str`
- `rules.python_apply(grid: list[list[int]], mode: str) -> list[list[int]]`
- `rules.counterfactual_program(kind: str) -> str`

- [ ] Add literal expected-grid tests for all four marker borders, packing around marker, and wrong-order/wrong-intermediate divergence.
- [ ] Run tests and confirm semantic failures.
- [ ] Implement the Python reference and exact Racket programs.
- [ ] Run focused tests through the packet Racket wrapper and confirm Python/Racket agreement.

### Task 3: Finite-rival teaching audit

**Files:**
- Create: `generators/148acacd84d9/workspace/parametric/self_audit.py`
- Modify: `generators/148acacd84d9/tests/test_parametric_gravity.py`

**Interfaces:**
- `self_audit.audit(out: Path, seeds=(0,17), demos=3, queries=4) -> dict`

- [ ] Add a test that two-demo lessons reject every named rival on demonstrations and all queries retain the selected answer.
- [ ] Confirm the test fails before audit/demo selection exists.
- [ ] Implement bounded protected-Racket evaluation for canonical, alternate, wrong-order, wrong-intermediate, skip-A, skip-B, opposite-edge, and one-step rivals.
- [ ] Run the audit and retain compact source-bound evidence.

### Task 4: Native qualification, causal witness, inventory, and packet result

**Files:**
- Create: task-local evidence under `workspace/parametric/evidence/current/`
- Create: `WORK/checks/148acacd84d9/qualification/{qualification.json,execution.json}`
- Create: `WORK/checks/148acacd84d9/causal/{witness.json,replay.json}`
- Modify: `generators/148acacd84d9/notes.md`
- Modify: `WORK/RESULTS.json`, `WORK/REVIEW.md`, `WORK/FEEDBACK_TO_CODEX.md`

- [ ] Run task tests and native qualification for every setting on seeds 0 and 17.
- [ ] Build and replay a wrong-intermediate witness using the qualified alternate program.
- [ ] Generate the source-bound manifest after evidence is final.
- [ ] Re-run focused tests, audit, qualification checks, public export checks, and package validation.
- [ ] Package only the delta and report owner acceptance as pending.
