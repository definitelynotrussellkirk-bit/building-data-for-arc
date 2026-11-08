# Workspace tools

`lesson_probe.py` is a source-bound adversarial curriculum probe. It loads the
current generator, iterates the generator's live `LESSON_COMPETITORS` and
`CANONICAL_SHORTCUTS`, checks all four cyclic starts of the schedule, and records
source hashes and exact failure seeds.

From `repo/`:

```sh
PYTHONPATH=shared/runtime python3 generators/55993f4c12af/workspace/lesson_probe.py \
  --cycles 25 --out ../checks/cyclic-lesson-probe.json
```

The retained final run covers 100 windows per band (300 total), all cyclic starts,
and reports zero ambiguous windows. This is finite rival testing, not a proof of
universal identifiability.
