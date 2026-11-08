# Task-local review workspace

The selected implementation is `../generator.py`. Files here are diagnostic
helpers and are never selected automatically.

## `lesson_probe.py`

A source-bound extended lesson census for the declared semantic competitors.
It loads the exact candidate path, records its SHA-256, labels generated inputs
with an independent 4-connected occupancy-boundary oracle, and tests every
entry in the generator's live `LESSON_COMPETITORS` declaration.

From the repository root:

```bash
PYTHONPATH=src:shared/runtime python3 \
  generators/b3bfd59c2c43/workspace/lesson_probe.py \
  --source generators/b3bfd59c2c43/generator.py \
  --lessons-per-band 100 \
  --json-out ../checks/lesson-probe-100-per-band.json
```

The default policy materializes 100 lessons in each of `easy`, `medium`, and
`hard`. Lesson `k` starts at sample index `11*k`, uses the generator's declared
`EXAMPLES_NEEDED` consecutive demonstrations, and then one query. Seeds are
SHA-256-derived independently for every band/lesson. The report includes:

- generator and corpus hashes;
- unique input count;
- self-check and independent-oracle disagreements;
- schedule-profile and semantic-witness counts;
- competitor survivors and query disagreements; and
- generator-declared lesson-identifiability failures.

Exit status is nonzero if any invalid grid, oracle mismatch, ambiguous lesson,
identifiability failure, or competitor survivor is found.
