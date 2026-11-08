# Reusable review tools

The production generator and the Racket label authority are separate. These tools
preserve that distinction and retain source-bound evidence for review.

## Focused regression tests

From the outer packet root, use the supported portable staging command:

```bash
python3 review.py check --stage task_tests --phase after --timeout 600 --out ../checks/task-tests-new
```

The selected interpreter must be Python 3.12+ with pytest, NumPy, and Pillow
importable when `PYTHONNOUSERSITE=1`. Use that same interpreter to invoke
`review.py`. The review retained the original prerequisite failure and the later
successful isolated-venv run. If only pytest and its pure-Python dependencies are
installed in the user site, `offline_test_env.py` can reuse those trusted installed
distributions in a new venv while keeping user-site isolation enabled:

```bash
python3 WORK/repo/generators/2006f915df8b/workspace/offline_test_env.py WORK/.review/new-test-python --receipt WORK/checks/new-test-environment.json
WORK/.review/new-test-python/bin/python review.py check --stage task_tests --phase after --timeout 600 --out ../checks/task-tests-new
```

This helper uses no network, modifies no base interpreter, and requires the base
interpreter's system NumPy and Pillow. It is not a package authenticity verifier.
The temporary venv and offline wheels are disposable and are not return artifacts.

## Source-pinned independent graph probe

```bash
python3 review.py run python3 generators/2006f915df8b/workspace/final_review_probe.py --out ../checks/graph-probe-new.json
```

This checks all 42 supported size pairs, four difficulty settings, seeds 0 and
6484, and raw indices 0–7. It uses independent Python BFS, not Racket labels.
It records unique-path inputs, witness refutation, accepted lesson windows,
query rotations, and None/default replay. Its source SHA is intentionally pinned;
update the probe deliberately if reviewing different generator bytes.

## Reference binding and retained regression

`../counterexamples/duplicate-6484/` contains the exact intermediate generator
that lost a teaching witness through duplicate rejection. The final return's
`checks/main-reference-racket.json` validates all five retained intermediate inputs
plus all five unchanged canonical labels. Its current-source metadata describes
the selected rule application; it does not claim those old inputs were generated
by the final source.

```bash
python3 WORK/repo/generators/2006f915df8b/workspace/verify_reference_evidence.py WORK/checks
```

This checks the saved public Racket outputs against the retained predictions,
including both findings-only audits. It requires the return's checks tree to be
restored at `WORK/checks/` and the issued audit generators to remain present.
It does not invoke Racket or retrieve solve query answers.

## Checkpoints

See `checkpoint-tool/README.md` for streaming create/restore, explicit exclusions,
original-ZIP identity verification, protected assignment/baseline handling,
conflict refusal, and the nine focused fixture tests. Store a checkpoint on a
filesystem that outlives the disposable execution session. A partial work tree
is useful for per-task checks but does not satisfy the full-source packaging gate.
