# Selected-task review tools

Selected implementation: `../generator.py`. Workspace files are explicit tools, not automatically selected alternative generators. Commands below run from the **extracted review packet root**, whose wrapper supplies Racket and changes into `repo`.

## Focused test runner

```bash
python3 run_with_racket.py python3 generators/d9d4f0ebb48b/workspace/review_checks.py test --out ../checks/task-tests-replay --phase replay
```

Creates an isolated runtime, explicitly stages all selected `test_*.py` files (including newly added tests missing from the frozen import map), then runs pytest with a concrete file list. Clears inherited PYTHONPATH, records the actual temporary cwd, staged generator hash, command and exit status, and removes the runtime. Receipts and run logs remain in the requested output directory. A green shared battery alone is not evidence that these new tests ran.

## Independent counterfactual probe

```bash
python3 run_with_racket.py python3 generators/d9d4f0ebb48b/workspace/review_checks.py palette --out ../checks/counterfactual-replay --samples 64 --phase replay
```

`palette_probe.py` samples all three bands, seeds `0..samples-1`, indexes 0–3, compares actual Racket outputs with the Python mirror and independently implemented palette/area bbox rivals, tests one zero-preserving nonzero-color relabeling per input, and checks four canonical pairs. Emits role histograms, unique-input counts, per-pair and complete-lesson survival, source hashes and full counterexample grids. **Any semantic finding exits nonzero.** Four-example groups are disjoint by `(band, seed)`; transformed inputs are derived, not additional independent samples. `--samples 1` is the small 28-reference-call smoke; `--samples 64` uses 1,540 calls.

To replay the original source in the provided review packet:

```bash
python3 run_with_racket.py python3 generators/d9d4f0ebb48b/workspace/review_checks.py palette --out ../checks/counterfactual-original-replay --samples 64 --phase before --generator-file ../.review/baseline/repo/generators/d9d4f0ebb48b/generator.py
```

The baseline probe is expected to fail the new semantic requirements. The original immutable baseline remains in the original packet; the return ZIP is a delta, not a second repository copy. The driver hashes the staged source **before** executing it, avoiding an editor/worker source race.

## Assigned audits, findings only

```bash
python3 run_with_racket.py python3 generators/d9d4f0ebb48b/workspace/adversarial_audit.py --out ../checks/audits-replay --samples 64
```

Checks only the two assigned targets (`2fb8d019f6ca`, `bc005ea27dae`) without modifying them. Uses three bands, seeds `0..samples-1`, index `1000+seed`, plus explicit ignored-override reproducers. Saves reference-backed witness grids and validation/domain status. Exit 0 means the audit completed, **not that no defect was found**. This is a scoped review utility, not a universal rule checker.

## Shared timeout diagnostic, no fix

```bash
python3 run_with_racket.py python3 generators/d9d4f0ebb48b/workspace/runtime_timeout_probe.py --out ../checks/runtime-timeout-replay.json
```

Measures ordinary Python versus `-S` startup and streaming termination at 0.2 and 1.0 seconds. Explains a failure in the shared timeout test without altering source or weakening acceptance. Retains actual stdout, callbacks, timeout status, runtime hash and cwd. Inspect findings instead of treating execution success as suite success.

## Evidence and limits

The original return includes red/green/intermediate logs, `REVIEW.md`, `DECISIONS.md`, `AUDIT.md`, `QUESTION_ANSWER.md`, feedback and exact executed commands in `RESULTS.json`. Source hashes, not stale historical phase labels, distinguish current evidence. No work here proves learner improvement or grants catalog/training approval. The canonical Racket authority is unchanged.
