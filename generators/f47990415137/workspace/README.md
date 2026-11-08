# Authoring probes — not solver inputs

These tools can read canonical or retained Racket answers. Do not import them
while performing a visible-only solve episode. No tool changes training approval.
Use the packet's wrapper from packet_root; payload paths are relative to repo.

## Independent rule and override regressions

`probe.py` provides a separately written BFS reference, canonical pairs via the
portable public helper, and grid observations. Run all selected tests:

```sh
python3 run_with_racket.py python3 -m pytest -q generators/f47990415137/tests
python3 run_with_racket.py python3 -m arcpuzzles check f47990415137 --stage task_tests --timeout 600 --phase after --out ../checks/task-tests-replay
```

## Query-role safety, reusable for another local task

`check_lesson_roles.py` consumes a completed source-bound lesson census and the
same generator file. It uses that generator's actual LESSON_COMPETITORS, scores
each pair once per rival, and tests every possible single-query role. Missing
rivals, empty/incomplete census data, source-hash mismatch and oracle differences
are errors, not semantic passes. Exit 1 reports ambiguity; exit 0 means none was
found among the declared rivals. A traceback/error must not be treated as a pass.
This is not an independent authentication of the labels or all sampler helpers;
it relies on the census's retained authority/provenance records.

```sh
python3 run_with_racket.py python3 generators/f47990415137/workspace/check_lesson_roles.py --census ../checks/lesson-census.json --generator generators/f47990415137/generator.py --out ../checks/role-coverage-replay.json --independent-aspect-oracle
python3 run_with_racket.py python3 generators/f47990415137/workspace/check_lesson_roles.py --census ../checks/audit/ba090ac77d54-census.json --generator generators/ba090ac77d54/generator.py --out ../checks/audit/ba090ac77d54-roles-replay.json
```

The second command intentionally exits 1: 108/360 optional role rotations remove
the sole demonstration distinguishing a conditional Euclidean rival. Original
production order has 0/72 ambiguous lessons. Only gate rotations actually used
by the exporter; rejecting a preserved ordering because an unused permutation
fails would be a false positive. Existing labels suffice; no new Racket calls
or model inference are needed. Reports retain the first 12 counterexamples;
the complete source-bound census retains every lesson for full regeneration.

## Ray-priority audit reproducer

`audit_ray.py` searches seeds 0..99 for a four-pair lesson whose first three pairs
also fit the wrong numeric-priority rule. It selects seed 2 and separately
reproduces ignored control requests at seed 17/sample 9. It writes Python
candidates, not authoritative findings. Verify with the supported public APIs:

```sh
python3 run_with_racket.py python3 generators/f47990415137/workspace/audit_ray.py ../checks/audit/311ebe067559
python3 run_with_racket.py python3 -m arcpuzzles apply 311ebe067559 --input ../checks/audit/311ebe067559/input.json --out ../checks/audit/311ebe067559/racket-replay.json
python3 run_with_racket.py python3 -m arcpuzzles generate 311ebe067559 --seed 2 --count 1 --train 3 --test 1 --difficulty medium --allow-unapproved --out ../checks/audit/311ebe067559/production-replay.jsonl
```

The audit target is unapproved. `--allow-unapproved` here materializes review
counterexamples only; it is not authorization to admit those lessons to training.
