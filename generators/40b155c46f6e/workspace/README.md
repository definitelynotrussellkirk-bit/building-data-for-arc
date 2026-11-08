# Source-bound review tools

Run from the **extracted review packet root**, after `python3 setup_racket.py`.
These tools require the supplied source tree and bundled runtime; this directory
alone is not a standalone ARC repository. They are reviewer diagnostics, not
training label authorities or training approval tools.

```sh
python3 -m pytest -q repo/generators/40b155c46f6e/tests
python3 run_with_racket.py python3 generators/40b155c46f6e/workspace/review_probe.py --mode final --seeds-per-band 40 --out ../checks/reproduced/final.json
python3 run_with_racket.py python3 generators/40b155c46f6e/workspace/review_probe.py --mode baseline --seeds-per-band 40 --out ../checks/reproduced/baseline.json
python3 run_with_racket.py python3 generators/40b155c46f6e/workspace/review_probe.py --mode audits --out ../checks/reproduced/audits.json
```

Use a new output path on each run. Existing reports are never overwritten.
Baseline mode needs `.review/baseline/.../generator.py` in the original assignment
packet; it never replaces the current source. Audit mode is bound to the two
unchanged random targets in `AUDIT_ASSIGNMENT.json` and makes findings only.
`--seeds-per-band` controls lesson modes; audit mode has a fixed 90-draw plan per
target. The outer wrapper changes cwd to `repo`; relative `--out` paths above
therefore intentionally start with `../checks/`.

`review_probe.py` prepares an independent runtime copy and starts an isolated
worker after clearing `PYTHONPATH`. `probe_worker.py` explicitly binds the
canonical Racket program, checks all canonical pairs and iterates the generator's
actual rivals/witness declarations. Default lesson evidence covers 40 seeds per
band and all three cyclic starts, three demos plus one query. Overlap is retained
and unique input counts are reported separately. `audit_worker.py` provides
findings-only frame-count, broken-border and same-row-domino reproducers. It
bootstraps only the copied runtime directory under isolated Python.

The report includes generator/rule/worker hashes, actual temporary cwd, seed
ranges, replay input hashes, unique counts and counterexample grids. Adjacent
`.execution.json` records exact argv/cwd and isolation flags; `.log` preserves
runtime output. Racket is mandatory for measured reports; a separate Python
oracle is used for cross-checks/tests only. Final lesson mode exits nonzero for
unrefuted declared rivals. Baseline mode permits survival to measure the old
defect; audit exit 0 means findings were reproduced, not that the targets passed.

A controlled regression replay without changing source:

```sh
env GENERATOR_UNDER_TEST=.review/baseline/repo/generators/40b155c46f6e/generator.py python3 -m pytest -q repo/generators/40b155c46f6e/tests/test_generator_40b155c46f6e.py
```

The expected retained baseline result is 33 failed / 23 passed. Final task tests
are 60 passed, including four audit-tool tests. Run root repository pytest
separately; it does not discover the task-local tests.

Do not consult these tools, the generator, canonical sources or old solve notes
during a fresh visible-only solve phase. Freeze generator edits, prepare a new
challenge, use visible examples only, and disclose earlier rule exposure.
