# Workspace

The selected implementation is ../generator.py. Workspace code is diagnostic.

## Probe cyclic lessons

From an extracted review packet root:

```bash
python3 run_with_racket.py python3 generators/89ab40aedfe4/workspace/probe_schedule.py \
  --seed-start 0 --seeds 10 --out ../checks/schedule-new.json
```

The output path must be new. To compare retained baseline bytes add
--generator ../checks/independent-review/baseline_generator.py when that evidence
file is available. The tool checks all four cyclic starts for four demonstrations
and one query, then holds out every pair. It reads actual CANONICAL_SHORTCUTS and
LESSON_COMPETITORS declarations and verifies their claimed canonical fits.

Labels are Python-mirror diagnostics, not Racket certification. The report binds
generator, probe and canonical hashes, seeds, actual directed indices, unique
inputs and exact first counterexamples. Exit 0 is a diagnostic pass; exit 1 means
ambiguity/canonical mismatch; exit 2 means execution or configuration error.
Missing rivals and incomplete execution are not a pass. It does not resample
failed lessons or run the production materializer.

For reference-backed production evidence, use:

```bash
python3 run_with_racket.py python3 -m arcpuzzles lesson-census 89ab40aedfe4 \
  --per-band 100 --rotate-query --timeout 1800 --out ../checks/census-new.json
```

Preserve ordinary and rotated verdicts separately. Finite declared-rival checks
do not prove uniqueness against arbitrary rules. For focused task regressions,
run the public check command with --stage task_tests so both portable and retained
legacy placements are exercised.
