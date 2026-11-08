# Workspace

`probe_distribution.py` is the reusable, source-bound lesson audit for this
repair. It imports the exact selected generator bytes, measures every generated
input, and labels the minimum declared witness subset needed for each lesson's
rival claim through public `Catalog.apply` canonical Racket execution. It
iterates the actual `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`,
`SEMANTIC_WITNESSES`, and `WITNESS_RIVALS` registries; no rival-name list or
correct-output Python implementation is copied into the tool.

From the packet root, a fast two-lesson-per-band smoke run is:

```bash
python3 run_with_racket.py python3 \
  generators/a6211f2301a7/workspace/probe_distribution.py \
  --lessons-per-start 1 --out ../checks/lesson-probe-smoke.json
```

The final audit uses 50 independent seeds at each curriculum start 0 and 1,
for 100 three-demonstration lessons per band:

```bash
python3 run_with_racket.py python3 \
  generators/a6211f2301a7/workspace/probe_distribution.py \
  --lessons-per-start 50 --out ../checks/lesson-probe-final.json
```

Every reported lesson/rival disagreement is backed by a public Racket label.
Unlabeled inputs contribute only distribution and uniqueness measurements.
The result is bounded to unforced default sampling, three demonstrations, both
parity starts, the declared finite rival set, and the declared input manifold;
it is not a universal induction claim.
