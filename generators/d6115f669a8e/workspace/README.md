# d6115f669a8e review workspace

`review_probe.py` is a source-bound lesson census for the repaired generator.
It imports the selected generator bytes, iterates the generator's actual
`CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, and tests every cyclic start of
the five-profile schedule. The default run covers **500 complete lessons per
band** (100 seed roots at each of five starts), records unique-input and profile
counts, verifies that declared canonical shortcuts really fit every canonical
pair, and reports any rival that survives a complete lesson.

High-volume rival scoring uses the task-local Python diagnostic mirror. A
bounded subset from every band/start and every canonical pair is independently
applied to the canonical Racket rule in the same process. This is finite
adversarial evidence over named rivals, not a claim of universal induction.

From the packet root:

```bash
python3 run_with_racket.py \
  python3 generators/d6115f669a8e/workspace/review_probe.py \
  --lessons-per-start 100 --racket-per-band 1 \
  --out ../checks/probe/d6115f669a8e_lesson_census.json
```

The tool refuses to overwrite evidence and binds its report to the exact
generator SHA-256, declared rule hash, canonical rule-source SHA-256, sampler,
seed range, sample-index formula, and domain limits.
