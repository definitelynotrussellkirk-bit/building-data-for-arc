# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Repeatable lesson diagnostics

`probe_lesson_windows.py` tests all cyclic starts of a declared period and all
single-query rotations, using the current generator's actual rival declarations
and Racket labels through the public API. It retains canonical-fit results,
source hashes, indices, unique inputs, and precise failures. It complements the
production sampler census: direct consecutive indices are not assumed to be
accepted production positions.

From the extracted packet root:

```sh
python3 run_with_racket.py python3 generators/f1668de79fa1/workspace/probe_lesson_windows.py --task f1668de79fa1 --seed-start 1000 --seeds 12 --period 3 --train 5 --bands easy,medium,hard --out ../checks/cyclic-windows.json
python3 run_with_racket.py python3 -m arcpuzzles lesson-census f1668de79fa1 --per-band 100 --rotate-query --timeout 1800 --out ../checks/lesson-census-next.json
python3 run_with_racket.py python3 -m arcpuzzles check f1668de79fa1 --stage task_tests --phase after --out ../checks/task-tests-next
```

Use new report paths for each source revision. The copied task-test runtime
finds canonical data through `reviewer_support.find_root` and
`reviewer_support.canonical_pairs`; no sibling checkout is required.
