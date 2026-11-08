# Task-local verification workspace

The selected implementation is `../generator.py`; these tools do not select alternate drafts. They prepare ordinary relocated runtimes from the packet and import only copied local sources.

From the extracted packet root, run:

```bash
python3 run_with_racket.py python3 generators/f16508733f0a/workspace/review_checks.py --out ../checks/focused-final --phase final --seeds 24
python3 run_with_racket.py python3 generators/f16508733f0a/workspace/review_checks.py --out ../checks/focused-tests --phase final --tests-only
python3 run_with_racket.py python3 generators/f16508733f0a/workspace/audit_assigned.py --out ../checks/audits
```

Use new output locations when retaining another run. `--no-racket` makes the census a Python-mirror diagnostic and labels its outputs accordingly. The test runner explicitly copies every task-local test, including files not listed in the baseline runtime map. Reports contain exact generator/rule hashes, canonical fit, named rival coverage, overlapping lesson windows, first witnesses and actual runtime directories.

`audit_assigned.py` is specific to this packet's two findings-only targets. It changes neither target and returns nonzero when an expected finding fails to reproduce. It is not a general safety certification.

The return package's `RESULTS.json` records actual commands and evidence. The full repository test suite must still be run separately; a green task-local run does not imply a green repository suite. Private solve labels and reference material are never opened by these verification tools.
