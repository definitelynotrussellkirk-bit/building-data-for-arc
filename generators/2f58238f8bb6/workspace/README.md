# Workspace

The selected implementation is `../generator.py`. Workspace code is not selected
as the generator automatically.

## Check a saved lesson without regenerating data

From the extracted packet root:

```sh
python3 repo/generators/2f58238f8bb6/workspace/check_lesson.py path/to/challenge.json --out checks/key-map-report.json
```

The file uses normal ARC `train` pairs and `test` queries. Only demonstration
outputs and query inputs are used. No Racket execution or model is needed. Exit
0 means the query maps agree within the eight-transform D4 class; exit 1 reports
missing teaching support; exit 2 means malformed input or another usage error.
The output path must be new. The report binds the generator and input-file
hashes. It does not independently certify demonstration labels or admit data.

For ordering, repetition and gallery rivals, use the existing full source-bound
lesson census. From the packet root:

```sh
python3 run_with_racket.py python3 -m arcpuzzles lesson-census 2f58238f8bb6 --per-band 100 --rotate-query --period 2 --out ../checks/new-census.json
python3 run_with_racket.py python3 -m arcpuzzles check 2f58238f8bb6 --stage task_tests --phase after --out ../checks/new-task-tests
```

Fixtures retain the baseline symmetry ambiguity and the repeated-key witness,
with original Racket provenance, for portable regression tests.
