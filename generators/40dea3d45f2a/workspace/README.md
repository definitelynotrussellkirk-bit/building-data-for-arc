# Task-local reusable verification

`probe.py` is an independent array-based D4 oracle plus a source-bound local census. It enumerates seeds and every cyclic start, reads the live rival declarations, and keeps demo-survival distinct from wrong-query survival. It can load a retained baseline with `--generator PATH`. An old generator with no declared rivals has empty dictionaries; its exit status alone must not be treated as a semantic certificate.

`lesson_probe.py` checks the real public Racket-backed `Catalog.generate` materializer. It rejects NO_CONTRACT, records complete episodes and accepted indices, and crosschecks actual labels against the array oracle. This code does not access private runtime entrypoints or silently change training approval.

From the **packet root**:

```sh
python3 run_with_racket.py python3 -m pytest -q generators/40dea3d45f2a/tests
python3 run_with_racket.py python3 generators/40dea3d45f2a/workspace/probe.py --seeds 100 --out ../checks/local-census.json
python3 run_with_racket.py python3 generators/40dea3d45f2a/workspace/lesson_probe.py --count 100 --seed 20261003 --out ../checks/public-lessons
python3 run_with_racket.py python3 -m arcpuzzles check 40dea3d45f2a --stage task_tests --timeout 600 --phase after --out ../checks/task-tests
```

The wrapper changes the child cwd to repo and supplies the offline Racket runtime. Direct invocations therefore use repo-relative paths. The portable task-tests stage uses a copied runtime and records its actual path and source hashes; do not infer that path from source depth.

Tests cover the equal-area witness, canonical support, exact controls and their provenance, all class/palette combinations, rejected invalid controls, connected D4 banks, all-five-rival windows, nonempty-panel policy, and no-contract/survivor reporting. The five canonical fixtures are retained for reproducibility; they are not generated query labels.

Finite-rival checks are not universal induction proofs. The teaching promise requires default consecutive draws. Ordinary sampling intentionally stays in connected monochrome 3–8-cell masks on this fixed layout.
