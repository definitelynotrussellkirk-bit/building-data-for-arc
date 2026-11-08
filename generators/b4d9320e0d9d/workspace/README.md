# b4d9320e0d9d review workspace

The selected implementation is `../generator.py`; focused regressions are in
`../tests/test_generator_b4d9320e0d9d.py`.

From the extracted packet root, replay the decisive checks with:

```sh
python3 run_with_racket.py python3 -m arcpuzzles check b4d9320e0d9d \
  --battery --timeout 4000 --phase after --out ../checks/after
python3 run_with_racket.py python3 -m arcpuzzles check b4d9320e0d9d \
  --stage task_tests --timeout 600 --phase after --out ../checks/task-tests
python3 run_with_racket.py python3 -m arcpuzzles check b4d9320e0d9d \
  --stage semantic_gate --require-rotations-identifiable --timeout 1800 \
  --phase after --out ../checks/required-rotations
python3 run_with_racket.py python3 -m arcpuzzles lesson-census b4d9320e0d9d \
  --per-band 100 --rotate-query --timeout 1800 \
  --out ../checks/lesson-census.json
```

The final generator hash is
`b2bd90b14c66887139bac83196d9f66f7805a99147e3353659bc424726fddf39`.
The selected Racket authority was not modified.
