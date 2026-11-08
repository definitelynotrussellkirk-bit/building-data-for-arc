## 536de2f7591b

**Outcome: `no_issue_found` within the bounded scope below.** No target files were edited. Generator version `3.1.0`, SHA-256 `c0f5598cf011e36aa5302bc3fd897c8f3fdc8851e043ccb64d05c4f5065fcf06`; canonical rule hash `02c227b9b2a6`.

### Scope and rationale

Read the selected `generator.py`, `notes.md`, and `evidence/review_index.json`; retrieved the four labeled canonical pairs using the public `reviewer_support.canonical_pairs` helper. The initial lookup for `_review_index.json` returned exit 1 because that spelling does not exist; the correct public index path is `evidence/review_index.json` and was read successfully. Historical success claims in the notes were treated as background, not as new verification.

The audited rule slides each contiguous green (3) row block immediately after its nearest original cyan (8) cell to the left, or to column zero when none exists. Length and lawful nonmarker cells remain unchanged. The audit uses an independently written Python mirror for bounded structural/rival checks and actual canonical Racket for representative authority checks.

| Check | Scope | Result |
|---|---|---|
| Default profiles | 48 cases: seeds 0, 1, 17; difficulty None/easy/medium/hard; all four profiles | Domain checks, deterministic replay, core canonical profile, and expected default witnesses passed |
| Single exact-control endpoints | 88 cases: seeds 0, 17; all four profiles; height 5/18, width 6/7/20, green-row count 1/6, block maximum 1/3, distractor count 0/3 | Every requested value observed exactly; all domain/replay checks passed |
| Crossed corners | 24 cases: all profiles in easy/hard, seed 17; tuples (h,w,rows,max,distractors) = (5,6,1,1,0), (18,20,6,3,3), (6,7,6,3,3) | All domain/replay/control checks passed |
| Documented incompatible overrides | h=5 with six green rows, all four profiles | Four expected `ValueError: n_green_rows cannot exceed grid_h` rejections |
| Declared-rival holdouts | 24 five-pair windows, five query positions each; seeds 0/17, None/easy/hard, four starting profiles | 0/120 ambiguous holdouts against suffix_only, any_nonzero_barrier, width_at_most_two, using mirror outputs |
| Canonical examples | Four publicly retrieved labeled pairs | All four agree with the independent mirror and with actual Racket |
| Actual canonical Racket | 22 inputs: 12 generated representatives, four canonical pairs, six hand boundaries | 22/22 output matches; no runtime errors; all valid outputs and valid generator-domain checks |

The six hand cases cover an interior block with only a right-side wall, the nearest of multiple left walls, an inert distractor in the travel path, a stationary adjacent-wall block, an overlapping source/destination shift, and a long shift of a width-three block. Inputs and actual outputs are retained, not just summaries.

### Interpretation

Width 6 is a valid exact override even for the path profile; it need not preserve that profile's default two-witness bundle. The notes explicitly exclude forced overrides from the default curriculum guarantee. Accordingly, loss of a default witness under a valid override was not labeled a defect. The h=5/six-row combination is explicitly incompatible and was rejected rather than clipped. No source-backed counterexample was found.

### Commands and observed results

Run from the packet's `WORK` directory; the wrapper executes payloads from `WORK/repo`. All three commands exited 0:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv-review/bin/python run_with_racket.py ../.venv-review/bin/python ../checks/audit/536de2f7591b/probe.py > checks/audit/536de2f7591b/probe.stdout.txt 2> checks/audit/536de2f7591b/probe.stderr.txt
PYTHONDONTWRITEBYTECODE=1 .venv-review/bin/python run_with_racket.py ../.venv-review/bin/python -m arcpuzzles apply 536de2f7591b --input ../checks/audit/536de2f7591b/inputs.json --check-generator-domain --timeout 120 --out ../checks/audit/536de2f7591b/racket.json > checks/audit/536de2f7591b/racket.stdout.txt 2> checks/audit/536de2f7591b/racket.stderr.txt
PYTHONDONTWRITEBYTECODE=1 .venv-review/bin/python run_with_racket.py ../.venv-review/bin/python ../checks/audit/536de2f7591b/finalize.py
```

The public apply receipt binds actual execution to canonical rule `02c227b9b2a6`, rule-text SHA-256 `32f99ab126f8942465379ea89224aae0c8a87e9ca7c66add45ae159a6a4897ab`, and the audited generator hash. The generator, notes, and review-index hashes were identical before and after the audit. `receipt.json` records source hashes, evidence hashes, commands, counts, and scope.

### Limits

This was a bounded audit, not a full battery or exhaustive proof. Only 22 representative cases used actual Racket; the remaining generation, invariant, and rival-rotation checks used the independent mirror. Rival identifiability was checked only against the three declared competitors. Arbitrary malformed inputs, blocks wider than three, disconnected green groups, collisions outside the declared grammar, and the proposed rightward parameter family were not investigated. No training-admission or catalog decision was changed.
