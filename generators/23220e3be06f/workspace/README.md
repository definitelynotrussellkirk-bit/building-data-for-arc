# 23220e3be06f review workspace

`reference_probe.py` is a reusable independent audit for the selected generator. It checks exact canonical examples, strict validation, determinism, command/palette/profile coverage, full D4 asymmetry, and optional parity against the protected Racket authority.

From the packet root:

```bash
python3 run_with_racket.py python3 \
  generators/23220e3be06f/workspace/reference_probe.py \
  --count 120 --racket --out ../checks/reference-probe.json
```

The payload runs from `repo/`; therefore the script path does not begin with `repo/`. The probe uses SHA-256-derived seeds and reports exact set/cardinality counts. Its Python mirror is diagnostic; output claims should be paired with `--racket` or the official `rule_smoke` stage.

The 46 portable regression tests live in `../tests/test_generator.py` and are run through the source-bound task-test stage:

```bash
python3 run_with_racket.py python3 -m arcpuzzles check 23220e3be06f \
  --stage task_tests --timeout 600 --phase after --out ../checks/task-tests
```
