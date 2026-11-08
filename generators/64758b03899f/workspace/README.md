# Task-local replay notes — 64758b03899f

The selected implementation is `../generator.py`. No alternate generator or private label source is stored here. The focused tests and retained counterexample are the reusable review tools.

From the packet root:

```bash
python3 run_with_racket.py python3 -m arcpuzzles check 64758b03899f \
  --stage task_tests --timeout 600 --phase after --out ../checks/task-tests
python3 run_with_racket.py python3 -m arcpuzzles check 64758b03899f \
  --stage semantic_gate --require-rotations-identifiable \
  --timeout 4000 --phase after --out ../checks/semantic-rotations-replay
python3 run_with_racket.py python3 -m arcpuzzles lesson-census 64758b03899f \
  --per-band 100 --rotate-query --rotation-policy require --timeout 1800 \
  --out ../checks/lesson-census-replay.json
python3 run_with_racket.py python3 -m arcpuzzles lesson-census 64758b03899f \
  --enumerate-schedule-period --rotate-query --rotation-policy require \
  --timeout 1800 --out ../checks/lesson-census-period-replay.json
```

The exact shortcut witness is `../counterexamples/first-mask-cell-origin.json`; its input-only form can be replayed through the canonical Racket authority with:

```bash
python3 run_with_racket.py python3 -m arcpuzzles apply 64758b03899f \
  --input generators/64758b03899f/counterexamples/first-mask-cell-origin.input.json \
  --out ../checks/selected-counterexample-racket-replay.json
```

`tests/test_generator.py` uses `reviewer_support.find_root` and `canonical_pairs`, so the canonical test is portable to the staged runtime. The schedule test exhausts multiple complete periods and every one-pair holdout; the shared period census separately binds the same claim to canonical Racket labels at all four declared start residues and three bands.
