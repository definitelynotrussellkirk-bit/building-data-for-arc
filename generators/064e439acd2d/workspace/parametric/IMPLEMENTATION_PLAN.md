# Projection Edge Mode Prototype and Scalar Contract Repair Implementation Plan

> **For agentic workers:** execute task-by-task with test-first changes. This packet has no Git metadata; preserve evidence in `WORK/checks/` and the final return ZIP instead of making commits.

**Goal:** Repair the selected generator's direct call-argument contract and add a separate runnable `edge_mode = near | far` prototype whose default is the unchanged canonical projection rule.

**Architecture:** The canonical generator gains only an entry-point validator for `seed` and `sample_index`; its sampler, deterministic version string, and Racket authority remain unchanged. The prototype lives under `workspace/parametric/`, loads the exact canonical Racket source for `near`, derives a complete `far` program by swapping only target-edge expressions, constructs fixed-per-episode examples from the selected generator, and executes both settings with the bundled Racket bridge.

**Tech Stack:** Python 3, pytest, bundled `arc_repl.racket_bridge.RacketBridge`, exact Racket source from `shared/data/canonical/puzzles.jsonl`.

**Spec:** `WORK/PARAMETRIC-RULES.md`; assignment duties from `python3 review.py duties`.

## Global Constraints

- Do not change shared runtime interfaces, the canonical Racket text, `RULE_HASH`, generator sampling semantics, or approval records.
- `near` must materialize byte-for-byte as the selected canonical `program_solution`; `far` changes only which bounding-box edge receives each aligned source color.
- Choose one hidden `edge_mode` deterministically from the episode seed and hold it fixed across every demonstration and query.
- Include complete episodes for both settings, with demonstrations distinguishing the alternative before an unlabelled public query.
- Derive retained labels by executing exact Racket, not by trusting a Python mirror.
- Public challenge JSON must omit hidden parameter values, reference code, and query outputs.
- Keep ordinary canonical repair evidence separate from prototype evidence.

## Review Focus

- Python `bool` values must not pass as integer `seed` or `sample_index`.
- Negative `sample_index` must reject while ordinary non-negative integer calls retain byte-identical outputs.
- The `near` source must remain exact canonical text and retain normalized hash `7288da9bfc7e`.
- The far transform must reverse both horizontal and vertical target edges without moving sources or painting diagonal decoys.
- Every retained prototype episode must use one mode and expose the near/far difference in labelled demonstrations and the query.

---

### Task 1: Direct call-argument contract

**Files:**
- Create: `repo/generators/064e439acd2d/tests/test_call_argument_contract.py`
- Modify: `repo/generators/064e439acd2d/generator.py`

**Interfaces:**
- Consumes: existing `generate(seed, sample_index, *, difficulty=None, **overrides)`.
- Produces: strict rejection of non-`int` seed/sample index and negative sample index, with valid outputs unchanged.

- [ ] Write tests covering invalid seed values `True`, `False`, `1.0`, `1.75`, and `"1"`; invalid sample indices `True`, `False`, `1.0`, `1.75`, and `-1`; and valid deterministic calls across `easy`, `None`, and `hard`.
- [ ] Run the focused tests and retain the expected pre-fix failure showing invalid calls are accepted.
- [ ] Add `_validate_call_arguments(seed, sample_index)` and invoke it before `_validate_overrides`; do not change `VERSION` or RNG inputs.
- [ ] Re-run the focused tests and the existing task tests; retain green receipts.

### Task 2: Fixed-per-episode edge-mode prototype

**Files:**
- Create: `repo/generators/064e439acd2d/tests/test_parametric_edge_mode.py`
- Create: `repo/generators/064e439acd2d/workspace/parametric/prototype.py`
- Create: `repo/generators/064e439acd2d/workspace/parametric/racket/near.rkt`
- Create: `repo/generators/064e439acd2d/workspace/parametric/racket/far.rkt`
- Create: `repo/generators/064e439acd2d/workspace/parametric/README.md`
- Generate: `repo/generators/064e439acd2d/workspace/parametric/examples/near_public.json`
- Generate: `repo/generators/064e439acd2d/workspace/parametric/examples/far_public.json`
- Generate: `checks/parametric/edge-mode-evidence.json`

**Interfaces:**
- Consumes: selected generator `generate`, canonical ledger `program_solution`, and `RacketBridge`.
- Produces: `choose_edge_mode(seed)`, `racket_source(mode, root=...)`, `python_transform(grid, mode)`, `build_episode(...)`, `public_challenge(...)`, and `build_report(...)`.

- [ ] Write prototype tests for allowed/default values, deterministic once-per-episode selection, exact canonical near source, setting-specific far source, complete discriminating episodes, hidden public fields, and exact retained Racket files.
- [ ] Run the focused test and retain the expected import/file failure before implementation.
- [ ] Implement the minimal standalone prototype and exact source materialization; use demonstration indices `(0, 2, 4, 6)` and query index `8` at medium difficulty.
- [ ] Run focused tests green.
- [ ] Execute the CLI through `review.py run`; require Racket/Python/episode agreement for both settings and write public challenge files.
- [ ] Inspect the retained report for exact source/hash, per-pair disagreement, and public redaction.

### Task 3: Full verification and handoff evidence

**Files:**
- Update: `repo/generators/064e439acd2d/notes.md`
- Create/update packet handoff files required by `review.py duties`.

**Interfaces:**
- Consumes: Tasks 1-2 and packet review tools.
- Produces: complete after-battery, task-test, solve, audit, result, replay, and packaged-return evidence.

- [ ] Run the after-repair battery and all task tests.
- [ ] Run the required lesson/schedule census and any assignment-specific probes.
- [ ] Complete the visible-only post-repair solve without consulting generator/reference source during that solve; record earlier exposure honestly.
- [ ] Run the two adversarial audits once and record findings without editing audited targets.
- [ ] Write `REVIEW.md`, `DECISIONS.md`, `QUESTION_ANSWER.md`, `AUDIT.md`, `FEEDBACK_TO_CODEX.md`, `RESULTS.json`, and concise current notes.
- [ ] Package the return ZIP, replay it against a fresh extraction, and verify the exact artifact hash and contents.
