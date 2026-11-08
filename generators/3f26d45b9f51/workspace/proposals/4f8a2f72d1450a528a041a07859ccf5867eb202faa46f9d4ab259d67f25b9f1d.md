# Review — `3f26d45b9f51` parametric extension
Task/source: `3f26d45b9f51` v4.0.0; production generator SHA-256 remains `1bd4448f9ff51545858cb402a42521bd7238925667727911e797a8259ee06f5a`.
Defect → repair: no retained parametric candidate → separate episode-level `axis_mode` prototype with `both_axes`, `horizontal_only`, and `vertical_only`.
Reference rule: unchanged; canonical rule hash remains `54129d31ff5b`, and the default program is byte-identical to canonical authority.
Production/training status: unchanged; the new artifact is explicitly `proposed_unapproved` and is not admitted to training.
Focused verification: staged task suite completed with 35/35 tests passing and exit code 0.
Evidence: 3 fixed-setting episodes, 9 demonstrations, 12 query cases (4 distinct inputs per episode), and 4/4 canonical-default labels matching real Racket execution.
Adversarial verification: 21/21 stored labels re-executed in Racket and matched an independent Python axis mirror; all declared rivals separated.
Export repair: duplicate visible payloads now fail before directory creation, and complete batches are sorted by exact visible-byte public ID.
Supplementary tickets: one parameter-query support check completed; one source-bound peer audit defect was reproduced for `2e9bbcd910a7`.
Assessment: selected-task work is routine and complete at prototype scope; maintainer attention is required only for variant approval and the separate peer finding.

## Built artifact

The new task-local prototype is `repo/generators/3f26d45b9f51/workspace/parametric/prototype.py`, with usage and boundary documentation in the adjacent `README.md`. It:

- preserves the exact canonical Racket program for `axis_mode=both_axes`;
- materializes explicit horizontal-only and vertical-only Racket siblings without editing production;
- chooses one setting per episode and holds it fixed across demonstrations and queries;
- draws deterministic, unique inputs from the approved production generator and accepts only inputs on which all three settings produce different real-Racket labels;
- verifies demonstration-only identifiability against the two declared rivals;
- exports exact visible challenge bytes separately from private settings, programs, provenance, and query answers;
- rejects duplicate visible payloads and existing output directories before writing; and
- records source/program/input/output hashes in a compact evidence report and manifest.

The regression suite is `repo/generators/3f26d45b9f51/tests/test_parametric_axis_mode.py`. It covers exact canonical default parity, invalid settings (including unhashable containers), hand-checked axis behavior, exact-integer controls, deterministic episode construction, four-query identifiability, visible-byte IDs, create-only export, public-ID ordering, manifest binding, and duplicate preflight.

## Verification actually run

All commands below were run from the outer packet root through `review.py`; their retained paths are relative to `WORK/`.

1. `python3 review.py check --stage task_tests --phase after --timeout 180 --out ../checks/parametric-final-task-tests`
   - Exit 0; 35 passed, 0 failed, 0 errors, 0 skipped in 16.06 seconds.
   - Evidence: `checks/parametric-final-task-tests/result.json`, `checks/parametric-final-task-tests/checks/task_tests.xml`.

2. `python3 review.py run python3 generators/3f26d45b9f51/workspace/parametric/prototype.py --seed 31 --all-settings --demo-count 3 --query-count 4 --out ../checks/parametric/axis-mode-final`
   - Exit 0; emitted three public/private episode pairs in public-ID order.
   - Evidence: `checks/parametric/axis-mode-final/report.json`, `checks/parametric/axis-mode-final/manifest.json`, `checks/parametric/axis-mode-final.command.txt`.

3. `python3 review.py run python3 ../checks/parametric/adversarial_probe.py --evidence ../checks/parametric/axis-mode-final --out ../checks/parametric/adversarial-result.json`
   - Exit 0; 21 Racket replays, 21 independent-mirror matches, 18 demonstration-rival comparisons, 24 query-rival comparisons, three privacy projections, sorted/unique public IDs, and strict boolean rejection.
   - Evidence: `checks/parametric/adversarial-result.json`, `checks/parametric/adversarial.command.txt`.

The retained evidence binds prototype SHA-256 `b411b5f9e0ee0032b245b1581d39712d89f440f09bd1cb4a337bc9e5ad7138ef` and the unchanged production generator SHA-256 above.

## Supplementary tickets

### `ticket-ddf325058e8fcf31` — completed support check

The pinned `8291f3ee7e54` evidence retained both fixed `ring_order` settings with two demonstrations and four distinct queries per setting. Public files matched exact visible-byte IDs; private seed/setting/program fields and query answers did not affect those IDs. This bounded evidence-only check did not re-execute Racket labels, approve the peer variant, or resolve its already reported physical creation-order gap. Evidence: `checks/tickets/ticket-ddf325058e8fcf31/result.json`.

### `ticket-e8b8b7cb6155e9e8` — reproduced peer finding

Against pinned generator SHA-256 `9301977697af1a47c63f609e71c4485d90002a7d15c32eb6f2470fc03ac1d8d6`, unknown override `typo_scene_family="tie_se"` was accepted for seed 19 / sample 23 / medium and returned the exact retained valid grid produced without the override. The bounded reproduction is recorded in `AUDIT.md`; no peer source was edited. Evidence: `checks/tickets/ticket-e8b8b7cb6155e9e8/result.json`.

## Remaining limits

The candidate covers only the three declared axis settings and retained seed 31; it is not a proof against arbitrary alternative rules. Its independent Python audit shares the production lattice parser, so a parser-correlated defect could survive both implementations. No production generator, canonical ledger row, shared runtime, approval state, or training set was changed. The next useful action is maintainer assessment of the candidate variant and separate owner triage of the peer unknown-override finding.
