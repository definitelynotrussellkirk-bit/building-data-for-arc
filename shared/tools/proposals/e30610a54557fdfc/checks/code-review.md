# Independent code review — 5639e60f0fac

Reviewed base `d9cc648` through head `e0920a9cbe7b8271256cee9535b1da534747dd07`.
Generator SHA-256: `9e77fa42b117a86ba45e717018b1fbb8996b2ad2b3b7c8adf2b6b2124a935dd7`.
This report describes that reviewed head; subsequent root fixes require their own verification.

**Assessment: changes requested for two Important tool defects.** No additional generator defect was found in the bounded review. Root confirmed both findings and is repairing them. No source, test, index, branch, assignment, or HEAD changes were made by this reviewer.

## Findings

### Critical

None found.

### Important R1 — Stored Racket inputs are not bound to the prepared inputs

**Location:** `WORK/repo/generators/5639e60f0fac/workspace/probe_role_positions.py:252–255` (also the resulting PASS at lines 268–281).

`score()` verifies source identity, the prepared payload, rule hashes, result count and sequential indices, then compares only result outputs. It never compares the public record's `input` or `input_sha256` with the corresponding prepared grid. The supported public apply result contains both fields (`WORK/repo/src/arcpuzzles/runtime.py:358–359`).

**Reproduction:** `checks/code-review/probe_gate_identity.py` prepares the real task inputs, builds a clearly synthetic parsing fixture, then replaces result 0's input with `[[0]]` and supplies that replacement grid's matching digest. Scoring still returns `PASS`. Removing both input identity fields from every result also returns `PASS`. The baseline synthetic fixture returns `PASS` as expected. These observations test parsing only; they are not Racket execution evidence.

**Impact:** A mismatched or incomplete stored result batch can be attributed to the prepared counterfactuals and produce a PASS. Comparing output values does not establish which inputs the authority evaluated. Require per-result input equality and a matching digest; validate the stored output digest and execution-error state as part of the same receipt check.

### Important R2 — The advertised prepare → apply command cannot consume its input file

**Location:** `WORK/repo/generators/5639e60f0fac/workspace/probe_role_positions.py:225–233,299–304`; advertised commands in `workspace/README.md:8–10` and the tool docstring at lines 5–7.

The prepare CLI writes the rich identity packet directly to `--out`. Public `arcpuzzles apply` accepts a grid, list, or an object with exactly one `input`/`inputs` key (`WORK/repo/src/arcpuzzles/runtime.py:298–306`). The prepared object has many metadata keys, so the documented pipeline stops before authority execution.

**Reproduction:** The same small probe calls the production `parse_apply_inputs(packet)`, which raises `object input must have exactly one key: "input" or "inputs"`. Passing `{"inputs": packet["inputs"]}` instead successfully parses all 15 cases. Root independently confirmed the actual public command exits 1 and retained that command failure.

**Impact:** The reusable CLI workflow cannot run as documented. Emit an apply-compatible file plus an identity sidecar, or explicitly provide another supported input artifact; scoring must bind the two together. The root's proposed bare payload plus `.meta.json` sidecar preserves the full-packet Python API while addressing this gap.

### Minor

None found.

## Checks actually performed

Commands ran from packet root `/dev/shm/arcpuzzles-f3b692803a21/round2` with exit code 0:

```bash
env PYTHONDONTWRITEBYTECODE=1 TMPDIR=/dev/shm/arcpuzzles-f3b692803a21/tmp2 PYTHONPATH=WORK/repo/shared/runtime WORK/.venv-review/bin/python WORK/checks/code-review/probe_gate_identity.py
env PYTHONDONTWRITEBYTECODE=1 TMPDIR=/dev/shm/arcpuzzles-f3b692803a21/tmp2 PYTHONPATH=WORK/repo/shared/runtime WORK/.venv-review/bin/python WORK/checks/code-review/probe_core_and_evidence.py
```

The independent core probe accepted all 3 canonical pairs (2 train, 1 test) and matched their stored labels with the Python mirror. It exercised 192 joint cases at minimum/maximum dimensions, combining every shape, family, quadrant and difficulty band; exact observations matched requests and outputs changed the canvas. Twelve invalid cell values, including boolean, float, container and missing values, produced diagnostics without crashing.

The crop implementation iterates every mask row and column, including column 4. Both positional shortcuts fit the canonical pairs, and the declared eight rivals are executable. The four-slot construction supplies two right-hand templates, two lower templates, two nonsquare templates and two masks asymmetric under all declared transforms. Any one-pair holdout preserves the required refuting examples. Object intervals remain feasible at height 8 and width 10, including width-4 masks.

Git JSON comparison found exactly one changed selected-solution field: `/racket_target/target_code`. The text change removes only `;; Sub-rectangle of the grid`; the resulting target equals the unchanged canonical program. All other selected JSON fields, including archival content, compare equal.

### Retained public evidence inspected, not rerun by this reviewer

| Evidence | Recorded coverage | Read-only checks |
|---|---:|---|
| `checks/after-final/checks/5639e60f0fac_after_battery_summary.json` | 12/12 green, required query rotations | Matching generator hash; 0 failed, advisory, pending or interrupted stages |
| `checks/lesson-census-final.json` | 300 lessons, 1,200 pairs, 1,200 query rotations; 1,185 unique inputs | Every accepted input digest matched; indices remained consecutive; 0 rejections; every recorded rival refuted |
| `checks/lesson-period-final.json` | 36 lessons, 144 pairs, 144 query rotations; 32 unique inputs | Fixed seed 0; starts 0–11 in every band; same identity, continuity, rejection and rival checks |

All lessons use 3 demonstrations and 1 query. The report records materialization through production `runner.run_one` and the selected canonical Racket rule. The review inspected that sampler's rejection/index handling and checked the saved sampling records. It did not rerun a Racket runtime or broad battery. Python mask predictions remain distinct from the retained authority evidence.

## Declined to judge — explicit root rulings and limits

- **Broader rule support:** three-row stencils and 3×3/3×4 footprints are the explicitly chosen bounded domain. Taller Racket-lawful inputs are outside this repair's promise.
- **Palette and placement expansion:** colors 3/8 are fixed semantic roles; ordinary placement separates both axes. Root has explicitly retained these choices. Exact overrides may bypass the teaching schedule as documented.
- **Difficulty ranking:** bands alter orientation support; no model or human difficulty ordering was claimed or evaluated.
- **Universal applicability or induction:** this tool is deliberately task-specific. Its legal-movement checks and mirror/authority comparisons support only the finite recorded witnesses. Stored JSON is not self-authenticating; external public-command provenance is still required. Generic position invariance and undeclared-rival identifiability were not certified.
- **Completion work:** final reports, audit/solve records, replay and packaging remain root reporting/handoff work, not defects merely because they were pending during this review. No solve private answers were inspected. No learning-uplift, training-admission, merge or publication judgment is made.
