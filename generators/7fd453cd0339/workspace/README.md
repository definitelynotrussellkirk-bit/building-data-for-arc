# Review workspace for `7fd453cd0339`

`reference_probe.py` supplies an independent component/bounding-box oracle, exact-axis observations, witness diffs, and an optional **real canonical Racket** batch executor. It is test tooling only; `generator.py` remains the selected implementation and Racket remains label authority.

From the repository root in a review packet/runtime:

```bash
pytest -q generators/7fd453cd0339/tests
```

The focused suite covers all public inputs, exact overrides, malformed inputs, every six-start/four-query curriculum rotation, all declared rivals, the retained counterexample, and Racket parity when the staged runtime is available. The portable official invocation is:

```bash
python3 -m arcpuzzles check 7fd453cd0339 \
  --stage task_tests --phase after --timeout 600 --out ../checks/task-tests
```

The exact semantic witness is retained at `../counterexamples/line-plus-same-color-rectangle.json`. Its `racket_evidence` field points to the review receipt that created the authoritative label; the focused test replays the generator case and every rival output without depending on that external path.
