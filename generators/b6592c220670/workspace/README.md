# Script repetition and lesson coverage review

Selected implementation: `../generator.py`, version `3.0.0`, SHA-256
`5447275c4a8eb23119a9357aa3d8933543d6a801f923152243545dd72c91a3f2`. Rule hash remains `042a7b2c96f6`.

`review_probe.py` is a reusable, source-bound audit, not a solver. It reads the
loaded source's actual `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`; verifies
canonical fits; generates 13 seeds × 12 draws × 3 bands; evaluates all eight
cyclic starts for four-demo/one-query lessons; and optionally checks every
output with the public `Catalog.apply` Racket API in batches of at most 64.
It refuses an existing output directory, records source hashes and exact sampling,
and retains source-bound reference receipts and a repetition counterexample.

From the packet root, after applying the returned patch:

```sh
python3 setup_racket.py
python3 run_with_racket.py python3 generators/b6592c220670/workspace/review_probe.py --oracle --phase replay --out ../checks/replay-census
python3 run_with_racket.py python3 -m arcpuzzles check b6592c220670 --stage task_tests --timeout 600 --phase after --out ../checks/replay-task-tests
```

Without `--oracle`, outputs come from the Python mirror and are not independent
reference evidence. `--generator PATH` allows a baseline snapshot, but oracle mode
requires the currently selected source to match that snapshot's hash. This is a
task-specific probe, not a promise to handle arbitrary generator interfaces.

Final result: 468 draws / 260 unique inputs across bands; 104 overlapping lessons
per band; every one of the 12 declared competitors is refuted by a demonstration
in every lesson. These are finite-family, finite-sample results, not universal
induction or independent lesson probabilities. The sampler still uses compact,
connected masks, and exact one-instruction overrides cannot teach repetition.
The first-code-1 general teaching slot ends in code 2 to rule out reversal.
