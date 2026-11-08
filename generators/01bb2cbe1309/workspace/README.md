# Workspace

The selected implementation is `../generator.py`.

## `lesson_probe.py`

A source-bound whole-lesson census for this task. It imports the final generator's actual `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, verifies each claimed shortcut against every usable canonical pair, then scores:

- the production lesson policy: one seed, demos at sample indices 0–3, query at 4;
- every cyclic start of the four-profile schedule;
- per-band dimensions, profile sequences, unique inputs, rival disagreements, and post-demo survivors.

Run from `repo`:

```bash
PYTHONPATH=shared/runtime python3 \
  generators/01bb2cbe1309/workspace/lesson_probe.py \
  --lessons-per-band 100 \
  --seed-start 0 \
  --out ../checks/01bb2cbe1309_final_lesson_census.json
```

The probe uses an independent Python oracle for scale. Cross-check that oracle with the repository `rule_smoke` and `semantic_gate` stages before trusting a census. Its conclusion is finite and source-hash-bound; it is not a claim of universal rule induction.
